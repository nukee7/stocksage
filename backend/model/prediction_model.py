# fixed_prediction_service.py
# THREAD-SAFE HYBRID LSTM + XGBOOST + SENTIMENT (Yahoo-only) — Guarded shapes

import os
import threading
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from ta.momentum import RSIIndicator
from ta.trend import MACD
import yfinance as yf
from transformers import pipeline

# --------------------------
# Threading / env limits
# --------------------------
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["XGBOOST_THREAD_POOL_SIZE"] = "1"
os.environ["TF_NUM_INTEROP_THREADS"] = "1"
os.environ["TF_NUM_INTRAOP_THREADS"] = "1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

_tf_lock = threading.Lock()

try:
    from threadpoolctl import threadpool_limits
except ImportError:
    threadpool_limits = None

# --------------------------
# Lazy heavy imports
# --------------------------
def _lazy_imports():
    import xgboost as xgb
    import tensorflow as tf
    from keras.models import Sequential
    from keras.layers import LSTM, Dense
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.threading.set_intra_op_parallelism_threads(1)
    return xgb, tf, Sequential, LSTM, Dense

# --------------------------
# Sentiment
# --------------------------
sentiment_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")

def get_stock_news_sentiment(ticker: str) -> pd.DataFrame:
    try:
        news_items = yf.Ticker(ticker).news
        if not news_items:
            return pd.DataFrame()
        rows = []
        for it in news_items[:10]:
            title = it.get("title", "")
            if not title:
                continue
            res = sentiment_pipeline(title)[0]
            lbl = res["label"].upper()
            score = {"POSITIVE": 1, "NEUTRAL": 0, "NEGATIVE": -1}.get(lbl, 0)
            rows.append({
                "date": datetime.fromtimestamp(it.get("providerPublishTime", datetime.now().timestamp())).date(),
                "score": score
            })
        df = pd.DataFrame(rows)
        return df.groupby("date")["score"].mean().reset_index() if not df.empty else pd.DataFrame()
    except Exception as e:
        print(f"[Sentiment error for {ticker}]: {e}")
        return pd.DataFrame()

# --------------------------
# Historical (Yahoo)
# --------------------------
def get_stock_historical_data(ticker: str, days: int = 90) -> pd.DataFrame:
    df = yf.download(ticker, period=f"{days}d", interval="1d", progress=False)
    if df is None or df.empty:
        print(f"[Yahoo] No historical data for {ticker}")
        return pd.DataFrame()

    # --- 🩹 Fix multi-index columns ---
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]  # flatten like ('Close', 'AAPL') -> 'Close'

    df.reset_index(inplace=True)

    expected_cols = {"Date", "Open", "High", "Low", "Close", "Volume"}
    if not expected_cols.issubset(df.columns):
        print(f"[Yahoo] fixed cols: {df.columns.tolist()}")
        return pd.DataFrame()

    return df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()

# --------------------------
# Feature engineering
# --------------------------
def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["SMA"] = df["Close"].rolling(window=10).mean()
    df["RSI"] = RSIIndicator(df["Close"]).rsi()
    df["MACD"] = MACD(df["Close"]).macd_diff()
    return df

def create_lag_features(df: pd.DataFrame, lags=(1,2,3)) -> pd.DataFrame:
    df = df.copy()
    for lag in lags:
        df[f"lag_{lag}"] = df["Close"].shift(lag)
    return df

# --------------------------
# Prepare data — GUARDED
# --------------------------
def prepare_data(df: pd.DataFrame, sentiment_df: pd.DataFrame):
    df = add_technical_indicators(df)
    df = create_lag_features(df)
    df = df.dropna().reset_index(drop=True)
    if df.empty:
        raise ValueError("No usable rows after indicator and lag creation (too few rows).")

    df["Date_only"] = df["Date"].dt.date
    if not sentiment_df.empty:
        df = df.merge(sentiment_df, how="left", left_on="Date_only", right_on="date")
        df["score"] = df["score"].fillna(0)
    else:
        df["score"] = 0.0

    features = ["SMA","RSI","MACD","lag_1","lag_2","lag_3","Volume","score"]
    target = "Close"

    X = df[features].values
    y = df[target].values  # 1D array here

    # enforce shapes
    if X.ndim != 2:
        raise ValueError(f"X must be 2D, got X.ndim={X.ndim}, shape={X.shape}")
    if y.ndim != 1:
        raise ValueError(f"y must be 1D before scaling, got shape={y.shape}")

    scaler_X = StandardScaler()
    X_scaled = scaler_X.fit_transform(X)

    scaler_y = MinMaxScaler()
    # scaler expects 2D, so reshape and keep 2D result
    y_2d = y.reshape(-1,1)
    y_scaled_2d = scaler_y.fit_transform(y_2d)  # shape (n_samples,1)

    # Return both y_scaled_2d and also flattened 1D version for algorithms expecting 1D
    return X_scaled, y_scaled_2d, y_scaled_2d.ravel(), df["Date"].values, scaler_X, scaler_y, df

# --------------------------
# Model training — guarded shapes
# --------------------------
def train_lstm(X, y_scaled_2d):
    xgb, tf_dummy, Sequential, LSTM, Dense = _lazy_imports()  # only to ensure TF also loaded
    X_lstm = np.reshape(X, (X.shape[0], 1, X.shape[1]))
    # Ensure y for LSTM is 2D with shape (n_samples, 1)
    if y_scaled_2d.ndim != 2 or y_scaled_2d.shape[1] != 1:
        raise ValueError(f"LSTM expects y_scaled_2d shape (n,1); got {y_scaled_2d.shape}")
    with _tf_lock:
        model = Sequential([
            LSTM(64, input_shape=(X_lstm.shape[1], X_lstm.shape[2])),
            Dense(1)
        ])
        model.compile(loss="mse", optimizer="adam")
        model.fit(X_lstm, y_scaled_2d, epochs=10, batch_size=8, verbose=0)
    return model

def train_xgboost(X, y_1d):
    xgb, *_ = _lazy_imports()
    # xgboost expects y to be 1D
    if y_1d.ndim != 1:
        raise ValueError(f"XGBoost expects y to be 1D, got shape {y_1d.shape}")
    model = xgb.XGBRegressor(
        n_estimators=80,
        random_state=42,
        verbosity=0,
        n_jobs=1,
        tree_method="hist",
        predictor="cpu_predictor",
    )
    model.fit(X, y_1d)
    return model

def safe_predict(model, X):
    with _tf_lock:
        return model.predict(X, verbose=0)

# --------------------------
# Predict future — guarded transforms
# --------------------------
def predict_future(X, lstm_model, xgb_model, scaler_y, dates, future_days=10):
    future_scaled = []
    last_X = X[-1].copy()

    for _ in range(future_days):
        # LSTM expects 3D input: (1,1,n_features)
        lstm_scaled_pred = safe_predict(lstm_model, np.reshape(last_X, (1,1,-1)))
        # ensure correct shape from LSTM: (1,1) or (1,1) -> take scalar
        try:
            lstm_scaled_val = float(np.asarray(lstm_scaled_pred).reshape(-1)[0])
        except Exception:
            raise ValueError(f"Unexpected LSTM output shape: {np.asarray(lstm_scaled_pred).shape}")

        # roll features and inject scaled lstm prediction
        new_features = np.roll(last_X, -1)
        new_features[-1] = lstm_scaled_val

        # XGBoost expects 2D features shape (1, n_features)
        hybrid_scaled = xgb_model.predict(new_features.reshape(1, -1))[0]
        future_scaled.append(hybrid_scaled)
        last_X = new_features

    # inverse-transform: scaler_y expects 2D array
    future_scaled_arr = np.array(future_scaled).reshape(-1,1)
    try:
        future_unscaled = scaler_y.inverse_transform(future_scaled_arr).reshape(-1)
    except Exception as e:
        raise ValueError(f"Error inverse transforming predictions: {e}")

    future_dates = [(pd.to_datetime(dates[-1]) + timedelta(days=i)).date() for i in range(1, future_days+1)]
    return pd.DataFrame({"Date": future_dates, "Predicted Price": future_unscaled})

# --------------------------
# Pipeline wrapper (threadpoolctl safe)
# --------------------------
def _pipeline_wrapper(func):
    if threadpool_limits:
        return threadpool_limits.wrap(limits=1, user_api="blas")(
            threadpool_limits.wrap(limits=1, user_api="openmp")(func)
        )
    return func

@_pipeline_wrapper
def generate_stock_prediction(ticker: str, days: int = 10):
    df = get_stock_historical_data(ticker, days=90)
    if df.empty:
        raise ValueError(f"No historical data found for {ticker}")

    sentiment_df = get_stock_news_sentiment(ticker)

    # prepare_data returns X_scaled, y_scaled_2d, y_scaled_1d, dates, scaler_X, scaler_y, df
    X_scaled, y_scaled_2d, y_scaled_1d, dates, scaler_X, scaler_y, df_full = prepare_data(df, sentiment_df)

    # sanity prints (or use logging)
    # print("Shapes:", X_scaled.shape, y_scaled_2d.shape, y_scaled_1d.shape)

    lstm_model = train_lstm(X_scaled, y_scaled_2d)
    xgb_model = train_xgboost(X_scaled, y_scaled_1d)

    predictions_df = predict_future(X_scaled, lstm_model, xgb_model, scaler_y, dates, future_days=days)
    current_price = float(df_full["Close"].iloc[-1])

    return {
        "ticker": ticker.upper(),
        "current_price": round(current_price, 2),
        "predictions": predictions_df["Predicted Price"].round(2).tolist(),
        "dates": predictions_df["Date"].astype(str).tolist(),
        "model": "Hybrid LSTM + XGBoost + Sentiment (Yahoo-only)"
    }