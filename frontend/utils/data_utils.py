import os
from datetime import datetime, timedelta
from polygon import RESTClient
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
    """Fetch stock price data for a given ticker."""
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
            "name": company_name
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
            "Ticker": ticker,
            "Shares": data["shares"],
            "Avg Price": f"${data['avg_price']:.2f}",
            "Current Price": f"${current_price:.2f}",
            "Value": f"${value:,.2f}",
            "Change %": f"{price_data['dp']}%",
            "Actions": ""
        })
    
    return portfolio_data, total_value
