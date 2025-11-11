from fastapi import HTTPException
from typing import Dict
from backend.service.stock_service import get_stock_price_service
from backend.model.portfolio_model import Portfolio

# You can store an in-memory global portfolio object
portfolio = Portfolio()


async def get_portfolio_holdings_service():
    """Return current portfolio holdings."""
    try:
        # Already returns {"holdings": [...]}
        return portfolio.get_holdings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching holdings: {str(e)}")


async def add_stock_service(ticker: str, shares: float, price: float):
    """Add/buy a stock to the portfolio."""
    try:
        portfolio.add_stock(ticker, shares, price)
        return {"message": f"Added {shares} shares of {ticker}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding stock: {str(e)}")


async def get_portfolio_value_service():
    """Get total portfolio performance summary."""
    try:
        performance = portfolio.get_portfolio_performance()
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating portfolio value: {str(e)}")