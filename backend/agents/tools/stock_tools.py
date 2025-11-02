from services.prediction_service import predict_stock
from services.sentiment_service import analyze_stock_sentiment
from services.portfolio_service import portfolio_recommendation

def get_stock_prediction(ticker: str):
    """Tool to fetch hybrid stock predictions."""
    try:
        return predict_stock(ticker)
    except Exception as e:
        return f"Prediction error: {e}"

def get_stock_sentiment(ticker: str):
    """Tool to fetch sentiment score for a company."""
    try:
        return analyze_stock_sentiment(ticker)
    except Exception as e:
        return f"Sentiment analysis error: {e}"

def get_portfolio_advice(portfolio_data: dict):
    """Tool to get portfolio rebalancing suggestions."""
    try:
        return portfolio_recommendation(portfolio_data)
    except Exception as e:
        return f"Portfolio advice error: {e}"