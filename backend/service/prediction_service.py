import numpy as np
import pandas as pd
from datetime import timedelta
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense
import xgboost as xgb
from .sentiment_service import get_stock_sentiments
from utils.data_utils import get_stock_historical_data, add_technical_indicators, create_lag_features


def prepare_data(df, sentiment_df):
    """Combine price data, technical indicators, and sentiment into feature matrix."""
    df = add_technical_indicators(df)
    df = create_lag_features(df)
    df = df.dropna()

    # Merge sentiment scores
    avg_sentiment = sentiment_df.groupby("date")["score"].mean().reset_index()
    df["date"] = df["t"].dt.date
    df = df.merge(avg_sentiment, how="left", on="date")
    df["score"] = df["score"].fillna(0)

    features = ["SMA", "RSI", "MACD", "lag_1", "lag_2", "lag_3", "v", "score"]
    target = "c"

    X = df[features]
    y = df[target]

    scaler_X = StandardScaler()
    X_scaled = scaler_X.fit_transform(X)

    scaler_y = MinMaxScaler()
    y_scaled = scaler_y.fit_transform(y.values.reshape(-1, 1)).flatten()

    return X_scaled, y_scaled, df["t"].values, scaler_X, scaler_y, df


def train_lstm(X, y):
    X_lstm = np.reshape(X, (X.shape[0], 1, X.shape[1]))
    model = Sequential()
    model.add(LSTM(64, input_shape=(1, X.shape[1]), return_sequences=False))
    model.add(Dense(1))
    model.compile(loss="mse", optimizer="adam")
    model.fit(X_lstm, y, epochs=10, batch_size=8, verbose=0)
    return model


def train_xgboost(X, y):
    xgb_model = xgb.XGBRegressor(n_estimators=100)
    xgb_model.fit(X, y)
    return xgb_model


def run_hybrid_prediction(ticker: str, start_date, end_date):
    """Main hybrid LSTM + XGBoost prediction pipeline."""
    hist_df = get_stock_historical_data(ticker, start_date, end_date)
    sentiment_df = get_stock_sentiments(ticker)

    if hist_df.empty:
        return {"error": "No stock data found for given range."}

    X, y, dates, scaler_X, scaler_y, df = prepare_data(hist_df, sentiment_df)

    lstm_model = train_lstm(X, y)
    xgb_model = train_xgboost(X, y)

    lstm_preds = lstm_model.predict(np.reshape(X, (X.shape[0], 1, X.shape[1]))).flatten()
    lstm_preds = scaler_y.inverse_transform(lstm_preds.reshape(-1, 1)).flatten()

    hybrid_input = np.concatenate([X, lstm_preds.reshape(-1, 1)], axis=1)
    hybrid_model = train_xgboost(hybrid_input, y)
    hybrid_preds = hybrid_model.predict(hybrid_input)
    hybrid_preds = scaler_y.inverse_transform(hybrid_preds.reshape(-1, 1)).flatten()

    # Future predictions
    future_days = 10
    last_X = X[-1]
    future_preds = []
    for _ in range(future_days):
        lstm_pred = lstm_model.predict(last_X.reshape(1, 1, -1)).flatten()[0]
        hybrid_input = np.concatenate([last_X.reshape(1, -1), np.array([[lstm_pred]])], axis=1)
        hybrid_pred = hybrid_model.predict(hybrid_input)[0]
        future_preds.append(hybrid_pred)
        last_X = np.roll(last_X, -1)
        last_X[-1] = lstm_pred

    future_preds = scaler_y.inverse_transform(np.array(future_preds).reshape(-1, 1)).flatten()
    future_dates = [(pd.to_datetime(dates[-1]) + timedelta(days=i)).date() for i in range(1, future_days + 1)]

    return {
        "ticker": ticker,
        "future_dates": future_dates,
        "future_predictions": future_preds.tolist(),
        "historical_predictions": hybrid_preds.tolist(),
    }