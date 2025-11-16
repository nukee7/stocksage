import asyncio
from langchain.agents import Tool
from backend.service.prediction_service import get_stock_prediction_service

async def _predict(symbol: str):
    return await get_stock_prediction_service(symbol)

StockPredictionTool = Tool(
    name="StockPredictionTool",
    func=lambda symbol: asyncio.run(_predict(symbol)),
    description="Get AI-based stock price predictions for a given symbol (e.g., AAPL, TSLA)."
)
