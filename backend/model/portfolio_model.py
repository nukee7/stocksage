from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import HTTPException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockHolding(BaseModel):
    """Represents a single stock holding in the portfolio."""
    symbol: str
    quantity: float
    average_price: float
    current_price: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    def update_price(self) -> None:
        """Fetch latest stock price using Yahoo Finance."""
        try:
            import yfinance as yf
            ticker = yf.Ticker(self.symbol)
            data = ticker.history(period="1d")
            
            if not data.empty:
                self.current_price = float(data["Close"].iloc[-1])
                self.last_updated = datetime.utcnow()
                logger.info(f"[Yahoo] Updated {self.symbol}: ${self.current_price:.2f}")
            else:
                logger.warning(f"[Yahoo] No data for {self.symbol}. Using average price.")
                self.current_price = self.average_price
                self.last_updated = datetime.utcnow()
        except Exception as e:
            logger.error(f"[Yahoo] Error fetching {self.symbol}: {e}")
            self.current_price = self.average_price
            self.last_updated = datetime.utcnow()

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


class Portfolio:
    """Portfolio manager for tracking stocks and cash."""
    
    def __init__(self, initial_cash: float = 100_000.0):
        self.holdings: Dict[str, StockHolding] = {}
        self.cash_balance: float = initial_cash
        self.initial_balance: float = initial_cash
        logger.info(f"Portfolio initialized with ${initial_cash:,.2f}")

    def add_stock(self, symbol: str, quantity: float, price: float) -> None:
        """
        Buy or add stock to the portfolio.
        
        Args:
            symbol: Stock ticker symbol
            quantity: Number of shares to buy
            price: Purchase price per share
        
        Raises:
            HTTPException: If insufficient cash balance
        """
        total_cost = quantity * price
        
        if total_cost > self.cash_balance:
            logger.error(f"Insufficient funds: Need ${total_cost:.2f}, have ${self.cash_balance:.2f}")
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient cash balance. Need ${total_cost:.2f}, have ${self.cash_balance:.2f}"
            )

        symbol = symbol.upper()
        
        if symbol in self.holdings:
            # Update existing holding
            existing = self.holdings[symbol]
            new_qty = existing.quantity + quantity
            new_avg_price = (
                (existing.average_price * existing.quantity) + (price * quantity)
            ) / new_qty
            
            logger.info(f"Adding to {symbol}: {quantity} shares @ ${price:.2f}")
            logger.info(f"  Old: {existing.quantity} @ ${existing.average_price:.2f}")
            logger.info(f"  New: {new_qty} @ ${new_avg_price:.2f}")
            
            existing.quantity = new_qty
            existing.average_price = new_avg_price
            existing.update_price()
        else:
            # Create new holding
            logger.info(f"New position: {symbol} - {quantity} shares @ ${price:.2f}")
            new_stock = StockHolding(
                symbol=symbol, 
                quantity=quantity, 
                average_price=price
            )
            new_stock.update_price()
            self.holdings[symbol] = new_stock

        # Deduct from cash
        self.cash_balance -= total_cost
        logger.info(f"Cash balance after purchase: ${self.cash_balance:,.2f}")

    def remove_stock(self, symbol: str, quantity: Optional[float] = None) -> None:
        """
        Sell stock partially or fully.
        
        Args:
            symbol: Stock ticker symbol
            quantity: Number of shares to sell (None = sell all)
        
        Raises:
            HTTPException: If stock not found or trying to sell more than owned
        """
        symbol = symbol.upper()
        
        if symbol not in self.holdings:
            logger.error(f"Stock {symbol} not found in portfolio")
            raise HTTPException(
                status_code=404, 
                detail=f"{symbol} not found in portfolio"
            )

        stock = self.holdings[symbol]
        stock.update_price()  # Get latest price before selling

        sell_qty = quantity if quantity is not None else stock.quantity
        
        if sell_qty > stock.quantity:
            logger.error(f"Cannot sell {sell_qty} shares of {symbol}, only own {stock.quantity}")
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot sell more than owned. You own {stock.quantity} shares."
            )

        # Calculate proceeds
        proceeds = sell_qty * stock.current_price
        self.cash_balance += proceeds
        
        logger.info(f"Selling {sell_qty} shares of {symbol} @ ${stock.current_price:.2f}")
        logger.info(f"Proceeds: ${proceeds:.2f}")
        logger.info(f"New cash balance: ${self.cash_balance:,.2f}")

        # Remove or update position
        if sell_qty >= stock.quantity:
            logger.info(f"Position fully closed: {symbol}")
            del self.holdings[symbol]
        else:
            stock.quantity -= sell_qty
            logger.info(f"Remaining position: {stock.quantity} shares of {symbol}")

    def update_prices(self) -> None:
        """Update current prices for all holdings."""
        logger.info("Updating all stock prices...")
        for stock in self.holdings.values():
            stock.update_price()

    def get_investments_value(self) -> float:
        """Get total market value of all investments."""
        self.update_prices()
        total = sum(stock.market_value for stock in self.holdings.values())
        logger.info(f"Total investments value: ${total:,.2f}")
        return total

    def get_portfolio_value(self) -> float:
        """Get total portfolio value (cash + investments)."""
        investments = self.get_investments_value()
        total = self.cash_balance + investments
        logger.info(f"Portfolio breakdown - Cash: ${self.cash_balance:,.2f}, Investments: ${investments:,.2f}, Total: ${total:,.2f}")
        return total

    def get_holdings(self) -> dict:
        """
        Return structured holdings list with all metrics.
        
        Returns:
            Dictionary containing list of holdings with calculated metrics
        """
        self.update_prices()
        total_investments = self.get_investments_value()
        
        # Avoid division by zero
        if total_investments == 0:
            total_investments = 1.0

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
        
        logger.info(f"Returning {len(holdings_list)} holdings")
        return {"holdings": holdings_list}

    def get_portfolio_performance(self) -> dict:
    """
    Return summarized portfolio performance with only invested amount and PnL.
    """
    self.update_prices()
    
    invested_value = self.get_investments_value()
    total_value = invested_value + self.cash_balance
    pnl = total_value - self.initial_balance
    pnl_percent = (pnl / self.initial_balance * 100) if self.initial_balance > 0 else 0.0

    performance = {
        "invested_value": round(invested_value, 2),
        "total_pnl": round(pnl, 2),
        "pnl_percent": round(pnl_percent, 2)
    }

    logger.info(f"Portfolio simplified performance: {performance}")
    return performance

    def get_summary(self) -> str:
        """Get a text summary of the portfolio."""
        perf = self.get_portfolio_performance()
        return f"""
Portfolio Summary:
- Total Value: ${perf['total_value']:,.2f}
- Cash Balance: ${perf['cash_balance']:,.2f}
- Invested: ${perf['invested_value']:,.2f}
- Holdings: {perf['holdings_count']}
- Total PnL: ${perf['total_pnl']:,.2f} ({perf['pnl_percent']:.2f}%)
        """.strip()