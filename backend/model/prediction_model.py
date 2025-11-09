import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from ta.momentum import RSIIndicator
from ta.trend import MACD

from backend.utils.data_utils import fetch_massive_data  # ✅ Unified Massive data fetcher

# ✅ Restrict threading early (safe for macOS)
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


# ======================================================
# 🧩 Helper: Lazy Importer
# ======================================================
def _lazy_imports():
    """
    Import heavy libraries (XGBoost, Keras) only when needed.
    Prevents blocking during FastAPI startup.
    """
    import xgboost as xgb
    from keras.models import Sequential
    from keras.layers import LSTM, Dense
    return xgb, Sequential, LSTM, Dense


# ======================================================
# 📊 Fetch Historical Data
# ======================================================
def get_stock_historical_data(ticker: str, days: int = 60) -> pd.DataFrame:
    ticker = ticker.upper()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    endpoint = (
        f"v2/aggs/ticker/{ticker}/range/1/day/"
        f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
    )

    try:
        data = fetch_massive_data(endpoint, {"sort": "asc"})
        results = data.get("results", [])
        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)
        df["t"] = pd.to_datetime(df["t"], unit="ms")
        df.rename(
            columns={"t": "Date", "o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"},
            inplace=True,
        )
        return df
    except Exception as e:
        print(f"[Error fetching data for {ticker}]: {e}")
        return pd.DataFrame()


# ======================================================
# 📈 Feature Engineering
# ======================================================
def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df["SMA"] = df["Close"].rolling(window=10).mean()
    df["RSI"] = RSIIndicator(df["Close"]).rsi()
    df["MACD"] = MACD(df["Close"]).macd_diff()
    return df


def create_lag_features(df: pd.DataFrame, lags=[1, 2, 3]) -> pd.DataFrame:
    for lag in lags:
        df[f"lag_{lag}"] = df["Close"].shift(lag)
    return df


# ======================================================
# 🧠 Data Preparation
# ======================================================
def prepare_data(df: pd.DataFrame):
    df = add_technical_indicators(df)
    df = create_lag_features(df)
    df = df.dropna()

    features = ["SMA", "RSI", "MACD", "lag_1", "lag_2", "lag_3", "Volume"]
    target = "Close"

    X = df[features].values
    y = df[target].values

    scaler_X = StandardScaler()
    X_scaled = scaler_X.fit_transform(X)

    scaler_y = MinMaxScaler()
    y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).flatten()

    return X_scaled, y_scaled, df["Date"].values, scaler_X, scaler_y, df


# ======================================================
# 🏗️ Model Training (Lazy Imports)
# ======================================================
def train_lstm(X, y):
    """Train LSTM with on-demand TensorFlow import."""
    _, Sequential, LSTM, Dense = _lazy_imports()

    X_lstm = np.reshape(X, (X.shape[0], 1, X.shape[1]))
    model = Sequential([
        LSTM(64, input_shape=(X_lstm.shape[1], X_lstm.shape[2]), return_sequences=False),
        Dense(1)
    ])
    model.compile(loss="mse", optimizer="adam")
    model.fit(X_lstm, y, epochs=10, batch_size=8, verbose=0)
    return model


def train_xgboost(X, y):
    """Train XGBoost lazily and safely."""
    xgb, _, _, _ = _lazy_imports()
    xgb_model = xgb.XGBRegressor(
        n_estimators=100,
        random_state=42,
        verbosity=0,
        n_jobs=1
    )
    xgb_model.fit(X, y)
    return xgb_model


# ======================================================
# 🔮 Prediction Logic
# ======================================================
def predict_future(X, lstm_model, hybrid_model, scaler_y, dates, future_days=10):
    future_predictions = []
    last_known_X = X[-1]

    for _ in range(future_days):
        lstm_pred = lstm_model.predict(np.reshape(last_known_X, (1, 1, -1)), verbose=0).flatten()[0]
        new_features = np.roll(last_known_X, -1)
        new_features[-1] = lstm_pred

        hybrid_pred = hybrid_model.predict(new_features.reshape(1, -1)).flatten()[0]
        future_predictions.append(hybrid_pred)
        last_known_X = new_features

    # Inverse transform
    future_predictions = scaler_y.inverse_transform(
        np.array(future_predictions).reshape(-1, 1)
    ).flatten()

    future_dates = [
        (pd.to_datetime(dates[-1]) + timedelta(days=i)).date()
        for i in range(1, future_days + 1)
    ]

    return pd.DataFrame({"Date": future_dates, "Predicted Price": future_predictions})


# ======================================================
# 🔧 Full Pipeline
# ======================================================
def generate_stock_prediction(ticker: str, days: int = 10):
    df = get_stock_historical_data(ticker, days=90)
    if df.empty:
        raise ValueError(f"No historical data found for {ticker}")

    X_scaled, y_scaled, dates, _, scaler_y, _ = prepare_data(df)

    # Lazy model training
    lstm_model = train_lstm(X_scaled, y_scaled)
    xgb_model = train_xgboost(X_scaled, y_scaled)

    predictions_df = predict_future(
        X_scaled, lstm_model, xgb_model, scaler_y, dates, future_days=days
    )
    current_price = float(df["Close"].iloc[-1])

    return {
        "ticker": ticker.upper(),
        "current_price": current_price,
        "predictions": predictions_df["Predicted Price"].round(2).tolist(),
        "dates": predictions_df["Date"].astype(str).tolist(),
        "model": "Hybrid LSTM + XGBoost (lazy on-demand)"
    }