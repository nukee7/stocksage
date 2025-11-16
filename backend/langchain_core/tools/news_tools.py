from langchain.agents import Tool
from backend.service.news_service import fetch_stock_news

def _fetch(symbol: str):
    return fetch_stock_news(symbol)

StockNewsTool = Tool(
    name="StockNewsTool",
    func=_fetch,
    description="Fetch the latest company news for a given stock symbol."
)
