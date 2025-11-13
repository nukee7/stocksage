from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field
from fastapi import HTTPException
import logging
import os
import yfinance as yf
import requests

# -------------------------------------------------------
# Logging setup
# -------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Finnhub API key (set this in your .env file)
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")


# -------------------------------------------------------
# StockHolding Model
# -------------------------------------------------------
class StockHolding(BaseModel):
    """Represents a single stock holding in the portfolio."""
    symbol: str
    quantity: float
    average_price: float
    current_price: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    # ---------------------
    # Price Fetch Methods
    # ---------------------
    def _fetch_price_yfinance(self) -> Optional[float]:
        """Fetch price from Yahoo Finance."""
        try:
            ticker = yf.Ticker(self.symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                return float(data["Close"].iloc[-1])
            logger.warning(f"[Yahoo] No data for {self.symbol}")
        except Exception as e:
            logger.error(f"[Yahoo] Error fetching {self.symbol}: {e}")
        return None

    def _fetch_price_finnhub(self) -> Optional[float]:
        """Fetch price from Finnhub as fallback."""
        if not FINNHUB_API_KEY:
            logger.warning("⚠️ FINNHUB_API_KEY not set — skipping Finnhub fallback.")
            return None

        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={self.symbol}&token={FINNHUB_API_KEY}"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                current = data.get("c")
                if current:
                    return float(current)
                logger.warning(f"[Finnhub] Empty quote data for {self.symbol}")
            else:
                logger.error(f"[Finnhub] Error {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"[Finnhub] Exception fetching {self.symbol}: {e}")
        return None

    def update_price(self) -> None:
        """Update stock price using Yahoo with Finnhub fallback."""
        try:
            price = self._fetch_price_yfinance()
            source = "Yahoo"

            if price is None:
                price = self._fetch_price_finnhub()
                source = "Finnhub" if price else "None"

            if price:
                self.current_price = price
                logger.info(f"[{source}] Updated {self.symbol}: ${self.current_price:.2f}")
            else:
                logger.warning(f"No price data found for {self.symbol}. Using average price.")
                self.current_price = self.average_price

            self.last_updated = datetime.utcnow()

        except Exception as e:
            logger.error(f"Error updating price for {self.symbol}: {e}")
            self.current_price = self.average_price
            self.last_updated = datetime.utcnow()

    # ---------------------
    # Computed Properties
    # ---------------------
    @property
    def market_value(self) -> float:
        """Current market value of this holding."""
        return self.quantity * self.current_price

    @property
    def cost_basis(self) -> float:
        """Total cost paid for this holding."""
        return self.quantity * self.average_price

    @property
    def pnl(self) -> float:
        """Profit/Loss in dollars."""
        return self.market_value - self.cost_basis

    @property
    def pnl_percent(self) -> float:
        """Profit/Loss as percentage."""
        return (self.pnl / self.cost_basis * 100) if self.cost_basis > 0 else 0.0


# -------------------------------------------------------
# Portfolio Model
# -------------------------------------------------------
class Portfolio:
    """Portfolio manager for tracking stocks and cash."""
    
    def __init__(self, initial_cash: float = 100_000.0):
        self.holdings: Dict[str, StockHolding] = {}
        self.cash_balance: float = initial_cash
        self.initial_balance: float = initial_cash
        logger.info(f"Portfolio initialized with ${initial_cash:,.2f}")

    # ---------------------
    # Portfolio Operations
    # ---------------------
    def add_stock(self, symbol: str, quantity: float, price: float) -> None:
        """Buy or add stock to the portfolio."""
        total_cost = quantity * price
        
        if total_cost > self.cash_balance:
            logger.error(f"Insufficient funds: Need ${total_cost:.2f}, have ${self.cash_balance:.2f}")
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient cash balance. Need ${total_cost:.2f}, have ${self.cash_balance:.2f}"
            )

        symbol = symbol.upper()
        
        if symbol in self.holdings:
            existing = self.holdings[symbol]
            new_qty = existing.quantity + quantity
            new_avg_price = (
                (existing.average_price * existing.quantity) + (price * quantity)
            ) / new_qty
            
            logger.info(f"Adding to {symbol}: {quantity} shares @ ${price:.2f}")
            existing.quantity = new_qty
            existing.average_price = new_avg_price
            existing.update_price()
        else:
            logger.info(f"New position: {symbol} - {quantity} shares @ ${price:.2f}")
            new_stock = StockHolding(symbol=symbol, quantity=quantity, average_price=price)
            new_stock.update_price()
            self.holdings[symbol] = new_stock

        self.cash_balance -= total_cost
        logger.info(f"Cash balance after purchase: ${self.cash_balance:,.2f}")

    def remove_stock(self, symbol: str, quantity: Optional[float] = None) -> None:
        """Sell stock partially or fully."""
        symbol = symbol.upper()
        
        if symbol not in self.holdings:
            raise HTTPException(status_code=404, detail=f"{symbol} not found in portfolio")

        stock = self.holdings[symbol]
        stock.update_price()
        sell_qty = quantity if quantity is not None else stock.quantity
        
        if sell_qty > stock.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot sell more than owned. You own {stock.quantity} shares."
            )

        proceeds = sell_qty * stock.current_price
        self.cash_balance += proceeds
        
        logger.info(f"Selling {sell_qty} shares of {symbol} @ ${stock.current_price:.2f}")
        logger.info(f"Proceeds: ${proceeds:.2f}")

        if sell_qty >= stock.quantity:
            del self.holdings[symbol]
        else:
            stock.quantity -= sell_qty

    # ---------------------
    # Portfolio Analytics
    # ---------------------
    def update_prices(self) -> None:
        """Update all stock prices."""
        logger.info("Updating all stock prices...")
        for stock in self.holdings.values():
            stock.update_price()

    def get_investments_value(self) -> float:
        """Get total market value of all holdings."""
        self.update_prices()
        return sum(stock.market_value for stock in self.holdings.values())

    def get_portfolio_value(self) -> float:
        """Total value = Cash + Investments."""
        investments = self.get_investments_value()
        return self.cash_balance + investments

    def get_holdings(self) -> dict:
        """Return structured holdings with metrics."""
        self.update_prices()
        total_investments = self.get_investments_value() or 1.0

        holdings_list = [
            {
                "symbol": s.symbol,
                "quantity": round(s.quantity, 4),
                "average_price": round(s.average_price, 2),
                "current_price": round(s.current_price, 2),
                "market_value": round(s.market_value, 2),
                "pnl": round(s.pnl, 2),
                "pnl_percent": round(s.pnl_percent, 2),
                "weight": round(s.market_value / total_investments * 100, 2),
                "last_updated": s.last_updated.isoformat(),
            }
            for s in self.holdings.values()
        ]

        return {"holdings": holdings_list}

    def get_portfolio_performance(self) -> dict:
        """Return summarized portfolio performance."""
        self.update_prices()

        invested_value = self.get_investments_value()
        total_value = invested_value + self.cash_balance
        pnl = total_value - self.initial_balance
        pnl_percent = (pnl / self.initial_balance * 100) if self.initial_balance > 0 else 0.0

        return {
            "invested_value": round(invested_value, 2),
            "total_value": round(total_value, 2),
            "cash_balance": round(self.cash_balance, 2),
            "total_pnl": round(pnl, 2),
            "pnl_percent": round(pnl_percent, 2),
            "holdings_count": len(self.holdings)
        }

    def get_summary(self) -> str:
        """Text summary for display."""
        perf = self.get_portfolio_performance()
        return f"""
Portfolio Summary:
- Total Value: ${perf['total_value']:,.2f}
- Cash Balance: ${perf['cash_balance']:,.2f}
- Invested: ${perf['invested_value']:,.2f}
- Holdings: {perf['holdings_count']}
- Total PnL: ${perf['total_pnl']:,.2f} ({perf['pnl_percent']:.2f}%)
        """.strip()