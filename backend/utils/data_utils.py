import os
import pandas as pd
from datetime import datetime, timedelta
from polygon import RESTClient
from ta.momentum import RSIIndicator
from ta.trend import MACD
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_polygon_client():
    """Initialize and return a Polygon.io client."""
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key:
        raise ValueError("Polygon.io API key not found. Please set the POLYGON_API_KEY in your .env file.")
    return RESTClient(api_key)


def get_stock_price(ticker):
    """Fetch current stock price data for a given ticker."""
    try:
        client = get_polygon_client()
        
        # Get previous close data
        prev_close = client.get_previous_close_agg(ticker, adjusted=True)
        if not prev_close or not prev_close.results:
            raise ValueError(f"No data returned from Polygon for {ticker}")
        
        current_price = prev_close.results[0].c  # closing price
        prev_close_price = prev_close.results[0].o  # open price of that day
        change_pct = ((current_price - prev_close_price) / prev_close_price) * 100

        # Get company info
        try:
            ticker_details = client.get_ticker_details(ticker)
            company_name = getattr(ticker_details, 'name', ticker)
        except Exception:
            company_name = ticker

        return {
            "c": current_price,
            "dp": round(change_pct, 2),
            "name": company_name,
            "error": None
        }
    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return {"c": 0, "dp": 0, "name": ticker, "error": str(e)}

def get_portfolio_value(portfolio):
    """Calculate portfolio value based on the given portfolio dictionary."""
    total_value = 0
    portfolio_data = []
    
    for ticker, data in portfolio.items():
        price_data = get_stock_price(ticker)
        current_price = price_data["c"]
        value = current_price * data["shares"]
        total_value += value
        
        portfolio_data.append({
            "ticker": ticker,
            "shares": data["shares"],
            "avg_price": data['avg_price'],
            "current_price": current_price,
            "value": value,
            "change_pct": price_data['dp']
        })
    
    return portfolio_data, total_value

def get_stock_historical_data(ticker, start, end):
    """Fetch historical stock data for a given ticker and date range."""
    try:
        client = get_polygon_client()
        
        # Convert dates to string format
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")
        
        # Get historical data
        response = client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=start_str,
            to=end_str,
            adjusted=True
        )
        
        if not response:
            return pd.DataFrame()
            
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': datetime.fromtimestamp(r.timestamp / 1000),
            'open': r.open,
            'high': r.high,
            'low': r.low,
            'close': r.close,
            'volume': r.volume
        } for r in response])
        
        return add_technical_indicators(df)
        
    except Exception as e:
        print(f"Error fetching historical data for {ticker}: {str(e)}")
        return pd.DataFrame()


def add_technical_indicators(df):
    """Add technical indicators to the DataFrame."""
    if df.empty:
        return df
        
    # Ensure we have enough data points
    if len(df) >= 10:
        df["sma_10"] = df["close"].rolling(window=10).mean()
    if len(df) >= 14:  # RSI typically uses 14 periods
        df["rsi"] = RSIIndicator(df["close"], window=14).rsi()
    if len(df) >= 26:  # MACD uses 26 and 12 periods
        df["macd"] = MACD(df["close"]).macd_diff()
    
    return df


def create_lag_features(df, lags=[1, 2, 3]):
    for lag in lags:
        df[f"lag_{lag}"] = df["c"].shift(lag)
    return df