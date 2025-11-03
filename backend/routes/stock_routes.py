from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime, timedelta
from utils.data_utils import fetch_massive_data

router = APIRouter()

# ---------- MODELS ----------
class PortfolioItem(BaseModel):
    ticker: str
    shares: float
    avg_price: float


class Portfolio(BaseModel):
    items: List[PortfolioItem]


# ---------- ROUTES ----------
@router.get("/stock/price/{ticker}")
async def get_stock_price(ticker: str):
    """
    Get current stock price and daily change percentage using Massive API.
    Returns: {"ticker": str, "name": str, "c": float, "dp": float}
    """
    ticker = ticker.upper()

    try:
        # --- Fetch basic ticker info ---
        data = fetch_massive_data(f"v3/reference/tickers/{ticker}")
        if not data or "results" not in data:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")

        ticker_info = data["results"]
        company_name = ticker_info.get("name", ticker)

        # --- Fetch previous close price ---
        prev_data = fetch_massive_data(f"v2/aggs/ticker/{ticker}/prev")
        prev_close = None
        if prev_data and "results" in prev_data and len(prev_data["results"]) > 0:
            prev_close = prev_data["results"][0].get("c")

        # --- Fetch latest trade price (fallback to prev_close if not available) ---
        trade_data = fetch_massive_data(f"v2/last/trade/{ticker}")
        current_price = None
        if trade_data and "results" in trade_data:
            current_price = trade_data["results"].get("p")

        current_price = current_price or prev_close or 0.0
        prev_close = prev_close or current_price

        # --- Compute daily % change ---
        daily_change = ((current_price - prev_close) / prev_close * 100) if prev_close else 0.0

        return {
            "ticker": ticker,
            "name": company_name,
            "c": round(current_price, 2),
            "dp": round(daily_change, 2)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stock price: {str(e)}")


@router.get("/stock/history/{ticker}")
async def get_stock_history(ticker: str, days: int = 30):
    """
    Get historical OHLCV data for the given ticker from Massive API.
    """
    ticker = ticker.upper()
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        endpoint = f"v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

        data = fetch_massive_data(endpoint, {"sort": "asc"})
        if not data or "results" not in data:
            raise HTTPException(status_code=404, detail=f"No historical data found for {ticker}")

        history = [
            {
                "date": datetime.fromtimestamp(item["t"] / 1000).strftime("%Y-%m-%d"),
                "open": item["o"],
                "high": item["h"],
                "low": item["l"],
                "close": item["c"],
                "volume": item["v"]
            }
            for item in data["results"]
        ]

        return {"ticker": ticker, "history": history, "period_days": days}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching historical data: {str(e)}")


@router.get("/stock/predict/{ticker}")
async def predict_stock(ticker: str, days: int = 10):
    """
    Simple stock price prediction using average daily change from last 30 days.
    """
    ticker = ticker.upper()
    try:
        price_data = await get_stock_price(ticker)
        current_price = price_data["c"]

        # --- Get last 30 days of price data ---
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        endpoint = f"v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        hist_data = fetch_massive_data(endpoint, {"sort": "asc"})

        if not hist_data or "results" not in hist_data:
            raise HTTPException(status_code=404, detail=f"No data for {ticker}")

        results = hist_data["results"]

        # --- Compute average daily change ---
        daily_changes = []
        for i in range(1, len(results)):
            prev_close = results[i - 1]["c"]
            curr_close = results[i]["c"]
            if prev_close > 0:
                daily_changes.append((curr_close - prev_close) / prev_close)

        avg_change = sum(daily_changes) / len(daily_changes) if daily_changes else 0.0

        # --- Generate predictions ---
        predictions = [current_price]
        dates = [datetime.now().strftime("%Y-%m-%d")]

        for i in range(1, days + 1):
            next_price = predictions[-1] * (1 + avg_change)
            predictions.append(round(next_price, 2))
            dates.append((datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"))

        return {
            "ticker": ticker,
            "current_price": round(current_price, 2),
            "predictions": predictions,
            "dates": dates,
            "avg_daily_change": round(avg_change * 100, 2)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting stock: {str(e)}")


@router.post("/portfolio/value")
async def calculate_portfolio_value(portfolio: Dict[str, Dict[str, float]]):
    """
    Calculate total portfolio value and per-stock metrics using Massive API.
    """
    try:
        portfolio_data = []
        total_value = 0.0

        for ticker, info in portfolio.items():
            price_data = await get_stock_price(ticker)
            current_price = price_data["c"]
            shares = info.get("shares", 0)
            avg_price = info.get("avg_price", 0)

            value = current_price * shares
            cost_basis = avg_price * shares
            gain_loss = value - cost_basis
            gain_loss_pct = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0.0

            portfolio_data.append({
                "ticker": ticker.upper(),
                "name": price_data["name"],
                "shares": shares,
                "avg_price": avg_price,
                "current_price": round(current_price, 2),
                "value": round(value, 2),
                "gain_loss": round(gain_loss, 2),
                "gain_loss_pct": round(gain_loss_pct, 2),
                "daily_change_pct": price_data["dp"]
            })

            total_value += value

        return {
            "portfolio": portfolio_data,
            "total_value": round(total_value, 2),
            "currency": "USD"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating portfolio value: {str(e)}")