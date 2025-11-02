from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import HTTPException
from polygon import RESTClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

if not POLYGON_API_KEY:
    raise ValueError("Polygon API key not found in .env file!")

# Initialize Polygon client
client = RESTClient(POLYGON_API_KEY)


class StockHolding(BaseModel):
    symbol: str
    quantity: float
    average_price: float
    current_price: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    def update_price(self):
        """Update the current price of the stock using Polygon.io."""
        try:
            # Try fetching the latest trade price
            trade = client.get_last_trade(self.symbol)
            self.current_price = trade.price
            self.last_updated = datetime.utcnow()
        except Exception as e:
            print(f"[WARN] Polygon last trade unavailable for {self.symbol}: {e}")
            # Fallback: use previous close if last trade data is restricted
            try:
                prev_close = client.get_previous_close_agg(self.symbol, adjusted=True)
                if prev_close and prev_close.results:
                    self.current_price = prev_close.results[0].c
                    self.last_updated = datetime.utcnow()
            except Exception as e2:
                print(f"[ERROR] Could not fetch any data for {self.symbol}: {e2}")
                self.current_price = self.average_price  # fallback

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


class Portfolio:
    def __init__(self, initial_cash: float = 100000.0):
        self.holdings: Dict[str, StockHolding] = {}
        self.cash_balance = initial_cash
        self.initial_balance = initial_cash
        self.transactions: List[dict] = []

    def add_stock(self, symbol: str, quantity: float, price: float) -> bool:
        """Add stock to portfolio and update its Polygon data."""
        total_cost = quantity * price
        if total_cost > self.cash_balance:
            raise HTTPException(status_code=400, detail="Insufficient cash balance")

        symbol = symbol.upper()
        if symbol in self.holdings:
            holding = self.holdings[symbol]
            new_quantity = holding.quantity + quantity
            new_avg_price = ((holding.average_price * holding.quantity) + (price * quantity)) / new_quantity
            holding.quantity = new_quantity
            holding.average_price = new_avg_price
            holding.update_price()
        else:
            holding = StockHolding(symbol=symbol, quantity=quantity, average_price=price)
            holding.update_price()
            self.holdings[symbol] = holding

        self.cash_balance -= total_cost
        self._record_transaction(symbol, "BUY", quantity, price, total_cost)
        return True

    def remove_stock(self, symbol: str, quantity: Optional[float] = None) -> bool:
        """Sell stock partially or completely."""
        symbol = symbol.upper()
        if symbol not in self.holdings:
            raise HTTPException(status_code=404, detail=f"{symbol} not found in portfolio")

        holding = self.holdings[symbol]
        holding.update_price()

        if quantity is None or quantity >= holding.quantity:
            quantity = holding.quantity
            total_value = holding.market_value
            del self.holdings[symbol]
        else:
            total_value = holding.current_price * quantity
            holding.quantity -= quantity

        self.cash_balance += total_value
        self._record_transaction(symbol, "SELL", quantity, holding.current_price, total_value)
        return True

    def update_prices(self) -> None:
        """Refresh all holdings prices using Polygon."""
        for holding in self.holdings.values():
            holding.update_price()

    def get_portfolio_value(self) -> float:
        """Return total value (cash + investments)."""
        return self.cash_balance + self.get_investments_value()

    def get_investments_value(self) -> float:
        return sum(holding.market_value for holding in self.holdings.values())

    def get_portfolio_performance(self) -> dict:
        """Return performance stats with updated prices."""
        self.update_prices()
        total_value = self.get_portfolio_value()
        total_pnl = total_value - self.initial_balance
        pnl_percent = (total_pnl / self.initial_balance * 100) if self.initial_balance > 0 else 0.0

        return {
            "total_value": total_value,
            "cash_balance": self.cash_balance,
            "invested_value": self.get_investments_value(),
            "total_pnl": total_pnl,
            "pnl_percent": pnl_percent,
            "initial_balance": self.initial_balance,
        }

    def get_holdings(self) -> List[dict]:
        """Return holdings with real-time Polygon data."""
        self.update_prices()
        total_investments = self.get_investments_value() or 1
        return [
            {
                "symbol": h.symbol,
                "quantity": h.quantity,
                "average_price": h.average_price,
                "current_price": h.current_price,
                "market_value": h.market_value,
                "pnl": h.pnl,
                "pnl_percent": h.pnl_percent,
                "weight": h.market_value / total_investments,
                "last_updated": h.last_updated.isoformat(),
            }
            for h in self.holdings.values()
        ]

    def _record_transaction(self, symbol, action, quantity, price, total_value):
        self.transactions.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": symbol,
                "action": action,
                "quantity": quantity,
                "price": price,
                "total_value": total_value,
                "cash_balance_after": self.cash_balance,
            }
        )

    def get_transaction_history(self) -> List[dict]:
        """Return list of all transactions."""
        return sorted(self.transactions, key=lambda x: x["timestamp"], reverse=True)


# Global portfolio instance
portfolio = Portfolio()