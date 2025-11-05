import logging
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import HTTPException
from time import sleep

from backend.utils.data_utils import fetch_massive_data


# ------------------------------------------------------------------
# 📈 StockHolding model (represents each stock in the portfolio)
# ------------------------------------------------------------------
class StockHolding(BaseModel):
    symbol: str
    quantity: float
    average_price: float
    current_price: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    # ------------------------
    # 🔄 Update Price
    # ------------------------
    def update_price(self) -> None:
        """Update stock price using Massive API daily data only, with safe fallback and backoff."""
        try:
            # Try daily OHLC data (most recent candle)
            endpoint = f"v2/aggs/ticker/{self.symbol}/range/1/day/2025-10-01/{datetime.now().strftime('%Y-%m-%d')}"
            for attempt in range(3):
                try:
                    data = fetch_massive_data(endpoint, {"sort": "desc", "limit": 1})
                    if data and "results" in data and len(data["results"]) > 0:
                        self.current_price = float(data["results"][0].get("c", 0.0))
                        self.last_updated = datetime.utcnow()
                        logging.info(f"[Massive] Updated price for {self.symbol}: {self.current_price}")
                        return
                except Exception as e:
                    if "429" in str(e):  # Handle rate limit
                        wait = 2 ** attempt
                        logging.warning(f"[Massive] Rate limited for {self.symbol}, retrying in {wait}s...")
                        sleep(wait)
                        continue
                    raise e
        except Exception as e:
            logging.warning(f"[Massive] Daily fetch failed for {self.symbol}: {e}")

        # Fallback → previous close
        try:
            prev_data = fetch_massive_data(f"v2/aggs/ticker/{self.symbol}/prev")
            if prev_data and "results" in prev_data and len(prev_data["results"]) > 0:
                self.current_price = float(prev_data["results"][0].get("c", 0.0))
                self.last_updated = datetime.utcnow()
                logging.info(f"[Massive] Prev close used for {self.symbol}: {self.current_price}")
                return
        except Exception as e:
            logging.warning(f"[Massive] Prev close fetch failed for {self.symbol}: {e}")

        # Final fallback → average price
        logging.error(f"[ERROR] No price found for {self.symbol}, using average price.")
        self.current_price = self.average_price
        self.last_updated = datetime.utcnow()

    # ------------------------
    # 📊 Computed Properties
    # ------------------------
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def cost_basis(self) -> float:
        return self.quantity * self.average_price

    @property
    def pnl(self) -> float:
        return self.market_value - self.cost_basis

    @property
    def pnl_percent(self) -> float:
        return (self.pnl / self.cost_basis * 100) if self.cost_basis > 0 else 0.0


# ------------------------------------------------------------------
# 💼 Portfolio model (manages all holdings)
# ------------------------------------------------------------------
class Portfolio:
    def __init__(self, initial_cash: float = 100_000.0):
        self.holdings: Dict[str, StockHolding] = {}
        self.cash_balance: float = initial_cash
        self.initial_balance: float = initial_cash

    # ------------------------
    # ➕ Add / ➖ Remove Stocks
    # ------------------------
    def add_stock(self, symbol: str, quantity: float, price: float) -> None:
        """Buy or add stock to the portfolio."""
        total_cost = quantity * price
        if total_cost > self.cash_balance:
            raise HTTPException(status_code=400, detail="Insufficient cash balance")

        symbol = symbol.upper()
        if symbol in self.holdings:
            existing = self.holdings[symbol]
            new_qty = existing.quantity + quantity
            new_avg_price = ((existing.average_price * existing.quantity) + (price * quantity)) / new_qty
            existing.quantity = new_qty
            existing.average_price = new_avg_price
            existing.update_price()
        else:
            new_stock = StockHolding(symbol=symbol, quantity=quantity, average_price=price)
            new_stock.update_price()
            self.holdings[symbol] = new_stock

        self.cash_balance -= total_cost

    def remove_stock(self, symbol: str, quantity: Optional[float] = None) -> None:
        """Sell stock partially or fully."""
        symbol = symbol.upper()
        if symbol not in self.holdings:
            raise HTTPException(status_code=404, detail=f"{symbol} not found in portfolio")

        stock = self.holdings[symbol]
        stock.update_price()

        sell_qty = quantity or stock.quantity
        if sell_qty > stock.quantity:
            raise HTTPException(status_code=400, detail="Cannot sell more than owned")

        proceeds = sell_qty * stock.current_price
        self.cash_balance += proceeds

        if sell_qty == stock.quantity:
            del self.holdings[symbol]
        else:
            stock.quantity -= sell_qty

    # ------------------------
    # 📈 Portfolio Stats
    # ------------------------
    def update_prices(self) -> None:
        for stock in self.holdings.values():
            stock.update_price()

    def get_holdings(self) -> List[dict]:
        """Return all holdings with updated prices."""
        self.update_prices()
        total_investments = self.get_investments_value() or 1.0
        return [
            {
                "symbol": s.symbol,
                "quantity": s.quantity,
                "average_price": s.average_price,
                "current_price": s.current_price,
                "market_value": s.market_value,
                "pnl": s.pnl,
                "pnl_percent": s.pnl_percent,
                "weight": s.market_value / total_investments,
                "last_updated": s.last_updated.isoformat(),
            }
            for s in self.holdings.values()
        ]

    def get_investments_value(self) -> float:
        return sum(stock.market_value for stock in self.holdings.values())

    def get_portfolio_value(self) -> float:
        return self.cash_balance + self.get_investments_value()

    def get_portfolio_performance(self) -> dict:
        """Return summarized performance metrics."""
        self.update_prices()
        total_value = self.get_portfolio_value()
        pnl = total_value - self.initial_balance
        pnl_percent = (pnl / self.initial_balance * 100) if self.initial_balance else 0.0
        return {
            "total_value": round(total_value, 2),
            "cash_balance": round(self.cash_balance, 2),
            "invested_value": round(self.get_investments_value(), 2),
            "total_pnl": round(pnl, 2),
            "pnl_percent": round(pnl_percent, 2),
            "initial_balance": round(self.initial_balance, 2),
        }