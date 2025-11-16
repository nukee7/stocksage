# backend/langchain_core/tools/stock_tools.py
import asyncio
from backend.service.prediction_service import get_stock_prediction_service

async def _predict(symbol):
    if symbol is None:
        return "No symbol provided."
    # if the wrapper passed a dict, extract symbol
    sym = symbol.get("symbol") if isinstance(symbol, dict) else str(symbol).strip()
    if not sym:
        return "No symbol provided."
    return await get_stock_prediction_service(sym)