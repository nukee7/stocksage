from datetime import datetime, timedelta
from fastapi import HTTPException
from backend.utils.data_utils import fetch_massive_data
from backend.model.prediction_model import generate_stock_prediction


# ---------- PRICE ----------
async def get_stock_price_service(ticker: str):
    """Get current price and daily % change from Massive API only."""
    ticker = ticker.upper()
    try:
        # --- Company info from Massive ---
        data = fetch_massive_data(f"v3/reference/tickers/{ticker}")
        company_name = data.get("results", {}).get("name", ticker) if data else ticker

        # --- Previous close ---
        prev_close = None
        try:
            prev_data = fetch_massive_data(f"v2/aggs/ticker/{ticker}/prev")
            if prev_data and "results" in prev_data and len(prev_data["results"]) > 0:
                prev_close = prev_data["results"][0].get("c")
        except Exception:
            prev_close = None

        # --- Latest price from Massive (intraday 1-min data) ---
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            intraday = fetch_massive_data(
                f"v2/aggs/ticker/{ticker}/range/1/minute/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}",
                {"sort": "desc", "limit": 1}
            )
            if intraday and "results" in intraday and len(intraday["results"]) > 0:
                current_price = intraday["results"][0].get("c")
            else:
                raise ValueError("No recent price data found")
        except Exception:
            raise HTTPException(status_code=404, detail=f"No recent data found for {ticker}")

        # --- Compute daily % change ---
        prev_close = prev_close or current_price
        daily_change = ((current_price - prev_close) / prev_close * 100) if prev_close else 0.0

        return {
            "ticker": ticker,
            "name": company_name,
            "c": round(current_price, 2),
            "dp": round(daily_change, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stock price: {str(e)}")


# ---------- HISTORY ----------
async def get_stock_history_service(ticker: str, days: int = 30):
    """Fetch OHLCV data for the last N days from Massive API."""
    ticker = ticker.upper()
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        endpoint = f"v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        data = fetch_massive_data(endpoint, {"sort": "asc"})

        if not data or "results" not in data:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")

        history = [
            {
                "date": datetime.fromtimestamp(item["t"] / 1000).strftime("%Y-%m-%d"),
                "open": item["o"],
                "high": item["h"],
                "low": item["l"],
                "close": item["c"],
                "volume": item["v"],
            }
            for item in data["results"]
        ]

        return {"ticker": ticker, "history": history, "period_days": days}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")


# ---------- PREDICTION ----------
async def predict_stock_service(ticker: str, days: int = 10):
    try:
        return generate_stock_prediction(ticker, days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# ---------- SELL ----------
async def sell_stock_service(ticker: str, shares: float, price: float):
    """Sell stock — integrate with portfolio instance."""
    from services.portfolio_service import portfolio
    try:
        portfolio.remove_stock(ticker, shares)
        return {"message": f"Sold {shares} shares of {ticker}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error selling stock: {str(e)}")