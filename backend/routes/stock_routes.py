from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Polygon API configuration
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
POLYGON_BASE_URL = "https://api.polygon.io"

class PortfolioItem(BaseModel):
    ticker: str
    shares: float
    avg_price: float

class Portfolio(BaseModel):
    items: List[PortfolioItem]

@router.get("/stock/price/{ticker}")
async def get_stock_price(ticker: str):
    """
    Get current stock price and daily change percentage
    Returns: {"c": current_price, "dp": daily_change_percent, "name": company_name}
    """
    if not POLYGON_API_KEY:
        raise HTTPException(status_code=500, detail="Polygon API key not configured")
    
    try:
        # Get current price from Polygon
        ticker = ticker.upper()
        
        # Get previous close
        url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{ticker}/prev"
        params = {"apiKey": POLYGON_API_KEY}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("resultsCount", 0) == 0:
            raise HTTPException(status_code=404, detail=f"No data found for ticker {ticker}")
        
        results = data["results"][0]
        prev_close = results["c"]
        
        # Get current/latest price
        current_url = f"{POLYGON_BASE_URL}/v2/last/trade/{ticker}"
        current_response = requests.get(current_url, params=params)
        current_response.raise_for_status()
        current_data = current_response.json()
        
        if "results" in current_data:
            current_price = current_data["results"]["p"]
        else:
            # Fallback to previous close if real-time not available
            current_price = prev_close
        
        # Calculate daily change percentage
        daily_change = ((current_price - prev_close) / prev_close) * 100
        
        # Get company name (ticker details)
        ticker_url = f"{POLYGON_BASE_URL}/v3/reference/tickers/{ticker}"
        ticker_response = requests.get(ticker_url, params=params)
        company_name = ticker
        
        if ticker_response.status_code == 200:
            ticker_data = ticker_response.json()
            if "results" in ticker_data:
                company_name = ticker_data["results"].get("name", ticker)
        
        return {
            "c": round(current_price, 2),
            "dp": round(daily_change, 2),
            "name": company_name,
            "ticker": ticker
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stock data: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/stock/predict/{ticker}")
async def predict_stock(ticker: str, days: int = 10):
    """
    Get stock price prediction for the next N days
    Returns: {"ticker": str, "current_price": float, "predictions": List[float], "dates": List[str]}
    """
    if not POLYGON_API_KEY:
        raise HTTPException(status_code=500, detail="Polygon API key not configured")
    
    try:
        ticker = ticker.upper()
        
        # Get current price first
        price_data = await get_stock_price(ticker)
        current_price = price_data["c"]
        
        # Get historical data for prediction (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        params = {"apiKey": POLYGON_API_KEY, "sort": "asc"}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("resultsCount", 0) == 0:
            raise HTTPException(status_code=404, detail=f"No historical data found for {ticker}")
        
        # Simple prediction model: calculate average daily change and project forward
        results = data["results"]
        daily_changes = []
        
        for i in range(1, len(results)):
            change = (results[i]["c"] - results[i-1]["c"]) / results[i-1]["c"]
            daily_changes.append(change)
        
        # Calculate average daily change and volatility
        avg_change = sum(daily_changes) / len(daily_changes) if daily_changes else 0
        
        # Generate predictions
        predictions = [current_price]
        prediction_dates = [datetime.now().strftime("%Y-%m-%d")]
        
        for i in range(1, days + 1):
            # Add some randomness to make it more realistic (simple model)
            predicted_price = predictions[-1] * (1 + avg_change)
            predictions.append(round(predicted_price, 2))
            
            future_date = datetime.now() + timedelta(days=i)
            prediction_dates.append(future_date.strftime("%Y-%m-%d"))
        
        return {
            "ticker": ticker,
            "current_price": current_price,
            "predictions": predictions,
            "dates": prediction_dates,
            "avg_daily_change": round(avg_change * 100, 2),
            "prediction_horizon_days": days
        }
        
    except HTTPException:
        raise
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stock data: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/portfolio/value")
async def calculate_portfolio_value(portfolio: Dict):
    """
    Calculate total portfolio value and individual stock values
    Expects: {"TICKER": {"shares": float, "avg_price": float}, ...}
    Returns: {"portfolio": List[dict], "total_value": float}
    """
    if not POLYGON_API_KEY:
        raise HTTPException(status_code=500, detail="Polygon API key not configured")
    
    try:
        portfolio_data = []
        total_value = 0
        
        for ticker, data in portfolio.items():
            # Get current price
            price_data = await get_stock_price(ticker)
            current_price = price_data["c"]
            daily_change = price_data["dp"]
            
            # Calculate values
            shares = data["shares"]
            avg_price = data["avg_price"]
            value = current_price * shares
            total_value += value
            
            # Calculate gain/loss
            cost_basis = avg_price * shares
            gain_loss = value - cost_basis
            gain_loss_pct = ((value - cost_basis) / cost_basis) * 100 if cost_basis > 0 else 0
            
            portfolio_data.append({
                "ticker": ticker,
                "name": price_data["name"],
                "shares": shares,
                "avg_price": avg_price,
                "current_price": current_price,
                "value": round(value, 2),
                "daily_change_pct": daily_change,
                "gain_loss": round(gain_loss, 2),
                "gain_loss_pct": round(gain_loss_pct, 2),
                "cost_basis": round(cost_basis, 2)
            })
        
        return {
            "portfolio": portfolio_data,
            "total_value": round(total_value, 2),
            "currency": "USD"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating portfolio value: {str(e)}")


@router.get("/stock/history/{ticker}")
async def get_stock_history(ticker: str, days: int = 30):
    """
    Get historical stock prices
    Returns: {"ticker": str, "history": List[{"date": str, "close": float, "volume": int}]}
    """
    if not POLYGON_API_KEY:
        raise HTTPException(status_code=500, detail="Polygon API key not configured")
    
    try:
        ticker = ticker.upper()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        params = {"apiKey": POLYGON_API_KEY, "sort": "asc"}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("resultsCount", 0) == 0:
            raise HTTPException(status_code=404, detail=f"No historical data found for {ticker}")
        
        history = []
        for result in data["results"]:
            history.append({
                "date": datetime.fromtimestamp(result["t"] / 1000).strftime("%Y-%m-%d"),
                "open": result["o"],
                "high": result["h"],
                "low": result["l"],
                "close": result["c"],
                "volume": result["v"]
            })
        
        return {
            "ticker": ticker,
            "history": history,
            "period_days": days
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching historical data: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")