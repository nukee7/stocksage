# backend/langchain_core/tools/stock_tools.py
from langchain.tools import Tool, StructuredTool
from pydantic.v1 import BaseModel, Field  # ✅ Use pydantic.v1 for LangChain compatibility
import requests

# ============================================
# 1. STOCK NEWS TOOL
# ============================================
class StockNewsInput(BaseModel):
    """Input for stock news queries"""
    symbol: str = Field(..., description="Stock ticker symbol (e.g., AAPL, TSLA)")

def get_stock_news(symbol: str) -> str:
    """Fetch latest news for a stock symbol"""
    try:
        response = requests.get(f"http://localhost:8001/api/news/{symbol}", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("news"):
            return f"No news found for {symbol}"
        
        news_list = []
        for article in data["news"][:5]:
            news_list.append(
                f"• {article['title']}\n"
                f"  {article['publisher']} - {article['providerPublishTime']}\n"
                f"  {article['link']}"
            )
        
        return f"Latest news for {symbol}:\n\n" + "\n\n".join(news_list)
    except Exception as e:
        return f"Error fetching news: {str(e)}"

StockNewsTool = StructuredTool.from_function(
    func=get_stock_news,
    name="StockNewsTool",
    description="Get the latest news articles for a stock. Use this when user asks about news, updates, or recent events for a specific stock ticker.",
    args_schema=StockNewsInput,
    return_direct=False,
)