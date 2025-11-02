from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from service.portfolio_service import portfolio, StockHolding, Portfolio

router = APIRouter()

class StockOrder(BaseModel):
    symbol: str
    quantity: float
    price: float

class PortfolioResponse(BaseModel):
    total_value: float
    cash_balance: float
    invested_value: float
    total_pnl: float
    pnl_percent: float
    initial_balance: float
    holdings: List[dict]
    transactions: List[dict]

@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio():
    """Get portfolio summary, holdings, and transactions."""
    performance = portfolio.get_portfolio_performance()
    holdings = portfolio.get_holdings()
    transactions = portfolio.get_transaction_history()
    
    return {
        **performance,
        'holdings': holdings,
        'transactions': transactions
    }

@router.post("/portfolio/buy")
async def buy_stock(order: StockOrder):
    """Buy a stock."""
    success = portfolio.add_stock(
        symbol=order.symbol,
        quantity=order.quantity,
        price=order.price
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    return {"message": f"Successfully bought {order.quantity} shares of {order.symbol} at ${order.price}"}

@router.post("/portfolio/sell")
async def sell_stock(order: StockOrder):
    """Sell a stock."""
    success = portfolio.remove_stock(
        symbol=order.symbol,
        quantity=order.quantity
    )
    
    if not success:
        raise HTTPException(status_code=404, detail=f"No position found for {order.symbol}")
    
    return {"message": f"Successfully sold {order.quantity} shares of {order.symbol}"}

@router.get("/portfolio/holdings", response_model=List[dict])
async def get_holdings():
    """Get all holdings in the portfolio."""
    return portfolio.get_holdings()

@router.get("/portfolio/transactions", response_model=List[dict])
async def get_transactions():
    """Get transaction history."""
    return portfolio.get_transaction_history()

@router.get("/portfolio/performance", response_model=dict)
async def get_performance():
    """Get portfolio performance metrics."""
    return portfolio.get_portfolio_performance()

@router.post("/portfolio/reset")
async def reset_portfolio(initial_balance: float = 100000.0):
    """Reset the portfolio with a new initial balance."""
    global portfolio
    portfolio = Portfolio(initial_balance=initial_balance)
    return {"message": f"Portfolio reset with initial balance: ${initial_balance:,.2f}"}