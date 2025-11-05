from fastapi import APIRouter
from pydantic import BaseModel
from backend.service.portfolio_service import (
    get_portfolio_holdings_service,
    add_stock_service,
    get_portfolio_value_service
)

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

class PortfolioAction(BaseModel):
    ticker: str
    shares: float
    price: float

@router.get("/holdings")
async def get_holdings():
    return await get_portfolio_holdings_service()

@router.post("/add")
async def add_stock(action: PortfolioAction):
    return await add_stock_service(action.ticker, action.shares, action.price)

@router.get("/value")
async def get_portfolio_value():
    return await get_portfolio_value_service()