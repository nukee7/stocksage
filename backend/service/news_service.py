import os
import requests
from datetime import datetime, timedelta
from fastapi import HTTPException

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

def fetch_stock_news(symbol: str):
    """
    Fetch latest company news from Finnhub for a given stock symbol.
    """
    if not FINNHUB_API_KEY:
        raise HTTPException(status_code=500, detail="Finnhub API key not configured")

    try:
        # Fetch last 7 days of news
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")

        url = (
            f"https://finnhub.io/api/v1/company-news"
            f"?symbol={symbol}&from={from_date}&to={to_date}&token={FINNHUB_API_KEY}"
        )

        response = requests.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Finnhub API error: {response.text}")

        news_data = response.json()
        if not isinstance(news_data, list) or len(news_data) == 0:
            raise HTTPException(status_code=404, detail=f"No news found for {symbol}")

        formatted_news = [
            {
                "title": item.get("headline", "No title"),
                "link": item.get("url", "#"),
                "publisher": item.get("source", "Unknown"),
                "providerPublishTime": datetime.fromtimestamp(item["datetime"]).strftime("%Y-%m-%d %H:%M:%S")
                if "datetime" in item else ""
            }
            for item in news_data
            if item.get("headline") and item.get("url")
        ]

        return {
            "symbol": symbol,
            "source": "Finnhub",
            "news": formatted_news
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"News fetch error: {str(e)}")