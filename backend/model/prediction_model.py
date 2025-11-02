import numpy as np
import pandas as pd
from datetime import timedelta

def predict_historical(X, y, lstm_model, xgb_model, scaler_y):
    """Generate hybrid model predictions on historical data"""
    lstm_preds = lstm_model.predict(np.reshape(X, (X.shape[0], 1, X.shape[1]))).flatten()
    lstm_preds = scaler_y.inverse_transform(lstm_preds.reshape(-1, 1)).flatten()

    hybrid_input = np.concatenate([X, lstm_preds.reshape(-1, 1)], axis=1)
    hybrid_preds = xgb_model.predict(hybrid_input).reshape(-1, 1)
    hybrid_preds = scaler_y.inverse_transform(hybrid_preds).flatten()

    return lstm_preds, hybrid_preds

def predict_future(X, lstm_model, hybrid_model, scaler_y, dates, future_days=10):
    """Predict future stock prices using hybrid approach"""
    future_predictions = []
    last_known_X = X[-1]

    for _ in range(future_days):
        lstm_pred = lstm_model.predict(np.reshape(last_known_X.reshape(1, 1, -1), (1, 1, -1))).flatten()[0]
        new_features = np.roll(last_known_X, -1)
        new_features[-1] = lstm_pred

        hybrid_input = np.concatenate([new_features.reshape(1, -1), np.array([[lstm_pred]])], axis=1)
        hybrid_pred = hybrid_model.predict(hybrid_input).flatten()[0]
        future_predictions.append(hybrid_pred)
        last_known_X = new_features

    future_predictions = scaler_y.inverse_transform(np.array(future_predictions).reshape(-1, 1)).flatten()
    future_dates = [(pd.to_datetime(dates[-1]) + timedelta(days=i)).date() for i in range(1, future_days + 1)]
    return pd.DataFrame({"Date": future_dates, "Predicted Price": future_predictions})