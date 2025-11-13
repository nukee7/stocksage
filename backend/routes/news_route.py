from fastapi import APIRouter
from backend.service.news_service import fetch_stock_news

router = APIRouter(prefix="/news", tags=["Stock News"])

@router.get("/{symbol}")
def get_stock_news(symbol: str):
    return fetch_stock_news(symbol.upper())