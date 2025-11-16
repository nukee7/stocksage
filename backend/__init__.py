"""
Backend package initialization
"""
# backend/__init__.py (very top)
# import os
# os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
from backend.routes import (
    portfolio_route,
    prediction_route,
    news_route,
    chatbot_route
)
