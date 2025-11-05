from fastapi import APIRouter
from pydantic import BaseModel
from backend.service.stock_service import (
    get_stock_price_service,
    get_stock_history_service,
    predict_stock_service,
    sell_stock_service
)

router = APIRouter(prefix="/stock", tags=["Stock"])

class TradeAction(BaseModel):
    ticker: str
    shares: float
    price: float

@router.get("/price/{ticker}")
async def get_stock_price(ticker: str):
    return await get_stock_price_service(ticker)

@router.get("/history/{ticker}")
async def get_stock_history(ticker: str, days: int = 30):
    return await get_stock_history_service(ticker, days)

@router.get("/predict/{ticker}")
async def predict_stock_price(ticker: str, days: int = 10):
    return await predict_stock_service(ticker, days)

@router.post("/sell")
async def sell_stock(action: TradeAction):
    return await sell_stock_service(action.ticker, action.shares, action.price)