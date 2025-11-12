from fastapi import HTTPException
import asyncio
from backend.model.prediction_model import generate_stock_prediction  # ✅ your existing model

async def get_stock_prediction_service(symbol: str, days: int = 10):
    """Call your existing Hybrid LSTM + XGBoost + Sentiment predictor safely."""
    try:
        # Run the heavy model in a background thread (non-blocking)
        result = await asyncio.to_thread(generate_stock_prediction, symbol, days)

        # Just return what your model already outputs — it’s already in the correct shape
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {e}")