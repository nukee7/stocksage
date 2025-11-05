import streamlit as st
import requests
import os
from datetime import datetime
import plotly.graph_objects as go
from dotenv import load_dotenv

# ----------------------------------
# Environment & Config
# ----------------------------------
env_path = os.path.join(os.path.dirname(__file__), "../../.env")
load_dotenv(env_path)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")

st.set_page_config(page_title="📊 Portfolio Dashboard", page_icon="💼", layout="wide")
st.title("💼 Portfolio Dashboard")
st.caption("Track, manage, and predict your stocks — all in one place.")

# ----------------------------------
# Backend Helper
# ----------------------------------
def call_backend(endpoint: str, method="GET", data=None):
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            res = requests.get(url, timeout=15)
        else:
            res = requests.post(url, json=data, timeout=15)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"Backend error: {e}")
        return None


# ----------------------------------
# Sidebar: Add Stock
# ----------------------------------
st.sidebar.header("➕ Add New Stock")

symbol = st.sidebar.text_input("Ticker Symbol (e.g. AAPL)").upper()
quantity = st.sidebar.number_input("Quantity", min_value=0.0, step=1.0)
price = st.sidebar.number_input("Buy Price ($)", min_value=0.0, step=0.1)

if st.sidebar.button("Add to Portfolio"):
    if symbol and quantity > 0 and price > 0:
        res = call_backend(
            "/api/portfolio/add",
            method="POST",
            data={"ticker": symbol, "shares": quantity, "price": price},
        )
        if res:
            st.sidebar.success(f"✅ {symbol} added successfully!")
            st.rerun()
    else:
        st.sidebar.warning("Please enter valid symbol, quantity, and price.")

if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()


# ----------------------------------
# Portfolio Holdings
# ----------------------------------
st.subheader("📊 Current Holdings")

holdings_data = call_backend("/api/portfolio/holdings")

if holdings_data and holdings_data.get("holdings"):
    holdings = holdings_data["holdings"]

    for idx, stock in enumerate(holdings):
        pnl_color = "green" if stock["pnl"] >= 0 else "red"

        with st.container():
            st.markdown(f"""
            <div style="background-color:white;border-radius:12px;padding:15px;margin:10px 0;
                        box-shadow:0 2px 6px rgba(0,0,0,0.1)">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <h4 style="margin:0">{stock['symbol']}</h4>
                        <small>Qty: {stock['quantity']}</small><br>
                        <small>Avg Price: ${stock['average_price']:.2f}</small>
                    </div>
                    <div style="text-align:right;color:{pnl_color}">
                        <b>${stock['current_price']:.2f}</b><br>
                        <small>{stock['pnl_percent']:.2f}%</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns([1, 1])

            # ---------- Prediction ----------
            with col1:
                if st.button(f"🔮 Predict {stock['symbol']}", key=f"predict_{idx}"):
                    with st.spinner(f"Predicting {stock['symbol']} trend..."):
                        pred = call_backend(f"/api/stock/predict/{stock['symbol']}")
                        if pred:
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=pred["dates"],
                                y=pred["predictions"],
                                mode="lines+markers",
                                name="Predicted"
                            ))
                            fig.add_hline(
                                y=pred["current_price"],
                                line_dash="dash",
                                line_color="red",
                                annotation_text=f"Current: ${pred['current_price']:.2f}"
                            )
                            fig.update_layout(
                                title=f"{stock['symbol']} - 10-Day Forecast",
                                template="plotly_white",
                                xaxis_title="Date",
                                yaxis_title="Price (USD)"
                            )
                            st.plotly_chart(fig, use_container_width=True)

            # ---------- Sell Stock ----------
            with col2:
                sell_qty = st.number_input(
                    f"Sell Qty ({stock['symbol']})",
                    min_value=0.0,
                    max_value=stock["quantity"],
                    step=1.0,
                    key=f"sell_qty_{idx}",
                )
                if st.button(f"💸 Sell {stock['symbol']}", key=f"sell_{idx}"):
                    if sell_qty > 0:
                        res = call_backend(
                            "/api/portfolio/sell",
                            method="POST",
                            data={"symbol": stock["symbol"], "quantity": sell_qty},
                        )
                        if res:
                            st.success(f"✅ Sold {sell_qty} {stock['symbol']}")
                            st.rerun()
                    else:
                        st.warning("Enter a valid sell quantity.")

            st.markdown("---")

else:
    st.info("No holdings found — add some stocks from the sidebar.")