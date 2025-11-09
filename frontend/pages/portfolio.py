import os
import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime
from dotenv import load_dotenv

# ----------------------------------
# Environment Setup
# ----------------------------------
env_path = os.path.join(os.path.dirname(__file__), "../../.env")
load_dotenv(env_path)

API_BASE_URL = "http://localhost:8001/api"

st.set_page_config(page_title="💼 Portfolio Dashboard", page_icon="💹", layout="wide")
st.title("💼 Portfolio Dashboard")
st.caption("Manage your holdings, track performance, and predict trends — all in one place.")

# ----------------------------------
# Helper: API Call Wrapper
# ----------------------------------
def call_backend(endpoint: str, method="GET", data=None):
    """Generic wrapper for backend requests with /api prefix."""
    url = f"{API_BASE_URL}{endpoint}"  # ensures /api prefix
    try:
        if method == "GET":
            res = requests.get(url, timeout=60)
        else:
            res = requests.post(url, json=data, timeout=60)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"⚠️ Backend error: {e}")
        return None

# ----------------------------------
# Sidebar - Add Stock Form
# ----------------------------------
with st.sidebar:
    st.header("➕ Add Stock to Portfolio")
    with st.form("add_stock_form"):
        ticker = st.text_input("Ticker Symbol", placeholder="AAPL, TSLA, NVDA").upper()
        quantity = st.number_input("Quantity", min_value=0.0, step=1.0)
        price = st.number_input("Buy Price ($)", min_value=0.0, step=0.1)
        submitted = st.form_submit_button("Add Stock")
        if submitted:
            if ticker and quantity > 0 and price > 0:
                with st.spinner(f"Adding {ticker}..."):
                    res = call_backend("/portfolio/add", method="POST", data={"ticker": ticker, "shares": quantity, "price": price})
                    if res:
                        st.success(f"✅ {ticker} added successfully!")
                        st.rerun()
            else:
                st.warning("Please fill all fields correctly.")

# ----------------------------------
# Portfolio Overview
# ----------------------------------
st.markdown("## 📊 Portfolio Overview")

holdings_data = call_backend("/portfolio/holdings")

if not holdings_data or not holdings_data.get("holdings"):
    st.info("No holdings yet. Add your first stock from the sidebar.")
else:
    holdings = holdings_data["holdings"]

    # Optional: Portfolio Performance
    perf = call_backend("/portfolio/value")
    if perf:
        total_value = perf.get("total_value", 0)
        pnl_percent = perf.get("pnl_percent", 0)
        st.metric("💰 Total Portfolio Value", f"${total_value:,.2f}", f"{pnl_percent:.2f}%")
        st.markdown("---")

    # Display holdings grid
    for stock in holdings:
        pnl_color = "green" if stock["pnl"] >= 0 else "red"

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1.5])

            with c1:
                st.subheader(stock["symbol"])
                st.caption(f"Avg Price: ${stock['average_price']:.2f}")
                st.caption(f"Quantity: {stock['quantity']:.0f}")

            with c2:
                st.metric("Current Price", f"${stock['current_price']:.2f}")

            with c3:
                st.metric("PnL %", f"{stock['pnl_percent']:.2f}%", delta_color="normal")

            with c4:
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(f"🔮 Predict", key=f"predict_{stock['symbol']}"):
                        with st.spinner(f"Generating forecast for {stock['symbol']}..."):
                            pred = call_backend(f"/stock/predict/{stock['symbol']}")
                            if pred:
                                fig = go.Figure()
                                fig.add_trace(go.Scatter(
                                    x=pred["dates"],
                                    y=pred["predictions"],
                                    mode="lines+markers",
                                    name="Predicted"
                                ))
                                fig.add_hline(y=pred["current_price"], line_dash="dash", line_color="red",
                                              annotation_text=f"Current: ${pred['current_price']:.2f}")
                                fig.update_layout(
                                    title=f"{stock['symbol']} - {len(pred['predictions'])}-Day Forecast",
                                    template="plotly_white",
                                    xaxis_title="Date",
                                    yaxis_title="Price (USD)",
                                    height=400
                                )
                                st.plotly_chart(fig, use_container_width=True)

                with col_b:
                    sell_qty = st.number_input(f"Sell Qty ({stock['symbol']})",
                                               min_value=0.0, max_value=stock["quantity"], step=1.0,
                                               key=f"sell_{stock['symbol']}")
                    if st.button(f"💸 Sell", key=f"sell_btn_{stock['symbol']}"):
                        if sell_qty > 0:
                            res = call_backend("/portfolio/sell", method="POST",
                                               data={"ticker": stock["symbol"], "shares": sell_qty, "price": stock["current_price"]})
                            if res:
                                st.success(f"✅ Sold {sell_qty} shares of {stock['symbol']}")
                                st.experimental_rerun()
                        else:
                            st.warning("Enter a valid quantity to sell.")