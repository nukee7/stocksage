"""
Model package initialization.
Includes model training and prediction functionality.
"""

from backend.utils.data_utils import get_stock_historical_data
from backend.service.sentiment_service import get_stock_sentiments
from .prediction_model import predict_future_prices

# Import any model-specific utilities
from .feature_engineering import prepare_data  # If this exists in your model directory

__all__ = [
    "get_stock_historical_data",
    "get_stock_sentiments",
    "prepare_data",
    "predict_future_prices"
]