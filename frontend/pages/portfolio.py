import streamlit as st
import pandas as pd
import requests
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load env vars
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

# Backend URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
BACKEND_URL = f"{API_BASE_URL}/api"

# Mock fallback portfolio
MOCK_PORTFOLIO = {
    "AAPL": {"shares": 10, "avg_price": 150.25},
    "MSFT": {"shares": 5, "avg_price": 300.50},
    "GOOGL": {"shares": 3, "avg_price": 2800.75},
    "AMZN": {"shares": 2, "avg_price": 3300.00}
}

# Streamlit setup
st.set_page_config(page_title="Portfolio | AI Financial Assistant", page_icon="📊", layout="wide")
st.title("📊 Portfolio Dashboard")
st.markdown("Track your investments and get AI-powered insights")

# ---- API helper functions ----
def fetch_backend(endpoint: str, method="GET", data=None, timeout=10):
    """Wrapper for backend requests with fallback"""
    url = f"{BACKEND_URL}{endpoint}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=timeout)
        elif method == "POST":
            r = requests.post(url, json=data, timeout=timeout)
        else:
            raise ValueError("Unsupported method")
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.warning(f"⚠️ Using mock data (backend error: {str(e)})")
        return None

def get_stock_price(ticker: str):
    resp = fetch_backend(f"/stock/price/{ticker}")
    if resp:
        return resp
    # Fallback mock
    import random
    return {"c": 150 + random.uniform(-10, 10), "dp": random.uniform(-3, 3), "name": ticker}

def get_stock_prediction(ticker: str):
    resp = fetch_backend(f"/stock/predict/{ticker}?days=10")
    if resp:
        return resp
    # Fallback mock
    base_price = 100
    return {
        "ticker": ticker,
        "current_price": base_price,
        "predictions": [base_price * (1 + 0.01 * i) for i in range(10)],
        "dates": [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(10)]
    }

def get_portfolio_value(portfolio):
    resp = fetch_backend("/portfolio/value", method="POST", data=portfolio)
    if resp:
        return resp
    # Fallback mock calc
    total_value = 0
    portfolio_data = []
    for t, d in portfolio.items():
        p = get_stock_price(t)
        value = d["shares"] * p["c"]
        total_value += value
        portfolio_data.append({
            "ticker": t,
            "shares": d["shares"],
            "avg_price": d["avg_price"],
            "current_price": p["c"],
            "value": value,
            "dp": p["dp"]
        })
    return {"portfolio": portfolio_data, "total_value": total_value}


# ---- Sidebar Health Check ----
try:
    resp = requests.get(f"{API_BASE_URL}/health", timeout=5)
    if resp.status_code == 200:
        st.sidebar.success("✅ Backend Connected")
    else:
        st.sidebar.warning("⚠️ Backend unhealthy")
except Exception:
    st.sidebar.error("❌ Backend Offline - Using mock data")

# ---- Refresh Button ----
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# ---- Portfolio Value ----
portfolio_response = get_portfolio_value(MOCK_PORTFOLIO)
portfolio_list = portfolio_response["portfolio"]
total_value = portfolio_response["total_value"]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Portfolio Value", f"${total_value:,.2f}")
with col2:
    st.metric("Daily Change", "+$1,234.56", "+2.34%")
with col3:
    st.metric("YTD Return", "+12.34%", "+$5,678.90")

# ---- Tabs ----
tab1, tab2 = st.tabs(["📈 Holdings", "🔍 Stock Analysis"])

# -----------------
# Tab 1: Holdings
# -----------------
with tab1:
    st.subheader("Your Holdings")

    if portfolio_list:
        cols = st.columns(2)
        for idx, stock in enumerate(portfolio_list):
            col = cols[idx % 2]
            with col:
                color_class = "positive" if stock["dp"] >= 0 else "negative"
                st.markdown(f"""
                <div style="background:white;border-radius:10px;padding:15px;margin-bottom:15px;box-shadow:0 2px 8px rgba(0,0,0,0.1)">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <div>
                            <h4>{stock['ticker']}</h4>
                            <p>Shares: {stock['shares']}</p>
                        </div>
                        <div class="{color_class}">
                            <b>${stock['current_price']:.2f}</b>
                            <span>({stock['dp']:+.2f}%)</span>
                        </div>
                    </div>
                    <p>Value: ${stock['value']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No holdings found.")

# -----------------
# Tab 2: Stock Analysis
# -----------------
with tab2:
    st.subheader("Stock Prediction")
    selected_ticker = st.selectbox("Select a stock", list(MOCK_PORTFOLIO.keys()))
    if st.button("Generate Prediction", type="primary"):
        with st.spinner("Generating prediction..."):
            data = get_stock_prediction(selected_ticker)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=data["dates"],
                y=data["predictions"],
                mode="lines+markers",
                name="Prediction"
            ))
            fig.add_hline(
                y=data["current_price"],
                line_dash="dash",
                line_color="red",
                annotation_text=f"Current: ${data['current_price']:.2f}"
            )
            fig.update_layout(title=f"{selected_ticker} 10-Day Forecast", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)