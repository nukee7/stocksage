from fastapi import APIRouter
from backend.service.prediction_service import get_stock_prediction_service

router = APIRouter(prefix="/predict", tags=["Stocks"])

@router.get("/{symbol}")
async def get_stock_prediction(symbol: str):
    return await get_stock_prediction_service(symbol)