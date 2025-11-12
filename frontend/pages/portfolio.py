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
        price = st.number_input("Buy Price ($)", min_value=0.0, step=0.01)
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
    
    st.markdown("---")
    
    # Refresh button
    if st.button("🔄 Refresh All Prices"):
        with st.spinner("Updating prices..."):
            call_backend("/portfolio/holdings")
            st.rerun()
    
    # Debug mode toggle
    show_debug = st.checkbox("🔍 Show Debug Info")

# ----------------------------------
# Portfolio Overview
# ----------------------------------
st.markdown("## 📊 Portfolio Overview")

# Fetch data
holdings_data = call_backend("/portfolio/holdings")
perf = call_backend("/portfolio/value")

# Debug: Print raw response
if show_debug:
    with st.expander("🔍 Raw API Response"):
        st.write("Holdings endpoint response:")
        st.json(holdings_data)
        st.write("Value endpoint response:")
        st.json(perf)

if not holdings_data:
    st.error("Unable to fetch portfolio data. Check if backend is running.")
elif not isinstance(holdings_data, dict):
    st.error(f"Unexpected data format from backend. Expected dict, got {type(holdings_data)}")
    if show_debug:
        st.json(holdings_data)
elif "holdings" not in holdings_data:
    st.error("Backend response missing 'holdings' key")
    if show_debug:
        st.json(holdings_data)
elif not holdings_data["holdings"] or len(holdings_data["holdings"]) == 0:
    st.info("No holdings yet. Add your first stock from the sidebar.")
    if perf and show_debug:
        st.json({"performance": perf})
else:
    holdings = holdings_data["holdings"]
    
    # Validate holdings is a list
    if not isinstance(holdings, list):
        st.error(f"Invalid holdings format. Expected list, got {type(holdings)}")
        if show_debug:
            st.json({"holdings_data": holdings_data, "holdings": holdings})
    else:
        # Debug: Check data structure
        if show_debug:
            st.write("DEBUG - Holdings count:", len(holdings))
            st.write("DEBUG - First holding:", holdings[0] if holdings else "None")

    # Portfolio Performance Metrics
    if perf:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_value = perf.get("total_value", 0)
            st.metric("💰 Total Portfolio Value", f"${total_value:,.2f}")
        
        with col2:
            cash_balance = perf.get("cash_balance", 0)
            st.metric("💵 Cash Balance", f"${cash_balance:,.2f}")
        
        with col3:
            invested_value = perf.get("invested_value", 0)
            st.metric("📈 Invested Value", f"${invested_value:,.2f}")
        
        with col4:
            pnl = perf.get("total_pnl", 0)
            pnl_percent = perf.get("pnl_percent", 0)
            st.metric("💹 Total PnL", f"${pnl:,.2f}", f"{pnl_percent:.2f}%")
        
        st.markdown("---")
    
    # Debug Information
    if show_debug:
        with st.expander("🔍 Debug Information"):
            st.json({"holdings": holdings_data, "performance": perf})
            
            # Manual calculation check
            total_market_value = sum(h["market_value"] for h in holdings)
            st.write(f"Manual calc - Invested Value: ${total_market_value:,.2f}")
            st.write(f"Backend - Invested Value: ${perf.get('invested_value', 0):,.2f}")
            st.write(f"Difference: ${abs(total_market_value - perf.get('invested_value', 0)):,.2f}")

    # Display holdings grid
    st.markdown("### 📋 Your Holdings")
    
    for idx, stock in enumerate(holdings):
        # Validate each stock is a dictionary
        if not isinstance(stock, dict):
            st.error(f"Invalid stock data at index {idx}: {type(stock)}")
            continue
            
        # Validate required fields
        required_fields = ["symbol", "quantity", "average_price", "current_price", "market_value", "pnl", "pnl_percent"]
        missing_fields = [field for field in required_fields if field not in stock]
        if missing_fields:
            st.error(f"Stock data missing fields: {missing_fields}")
            if show_debug:
                st.json(stock)
            continue
                
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1.5])

            with c1:
                st.subheader(stock["symbol"])
                st.caption(f"Avg Price: ${stock['average_price']:.2f}")
                st.caption(f"Quantity: {stock['quantity']:.2f}")
                if show_debug:
                    st.caption(f"Last Updated: {stock.get('last_updated', 'N/A')}")

            with c2:
                st.metric("Current Price", f"${stock['current_price']:.2f}")
                st.caption(f"Market Value: ${stock['market_value']:.2f}")

            with c3:
                pnl_delta = f"{stock['pnl_percent']:.2f}%"
                st.metric("PnL", f"${stock['pnl']:.2f}", pnl_delta)
                st.caption(f"Weight: {stock.get('weight', 0):.1f}%")

            with c4:
                col_a, col_b = st.columns(2)
                
                with col_a:
                    if st.button(f"🔮 Predict", key=f"predict_{stock['symbol']}"):
                        with st.spinner(f"Generating forecast for {stock['symbol']}..."):
                            # Route is /api/predict/{symbol} - call_backend already adds /api
                            pred = call_backend(f"/predict/{stock['symbol']}")
                            if pred:
                                fig = go.Figure()
                                fig.add_trace(go.Scatter(
                                    x=pred["dates"],
                                    y=pred["predictions"],
                                    mode="lines+markers",
                                    name="Predicted",
                                    line=dict(color='royalblue', width=2)
                                ))
                                fig.add_hline(
                                    y=pred["current_price"], 
                                    line_dash="dash", 
                                    line_color="red",
                                    annotation_text=f"Current: ${pred['current_price']:.2f}"
                                )
                                fig.update_layout(
                                    title=f"{stock['symbol']} - {len(pred['predictions'])}-Day Forecast",
                                    template="plotly_white",
                                    xaxis_title="Date",
                                    yaxis_title="Price (USD)",
                                    height=400,
                                    showlegend=True
                                )
                                st.plotly_chart(fig, use_container_width=True)

                with col_b:
                    sell_qty = st.number_input(
                        f"Sell Qty",
                        min_value=0.0, 
                        max_value=stock["quantity"], 
                        step=1.0,
                        key=f"sell_{stock['symbol']}",
                        label_visibility="collapsed"
                    )
                    if st.button(f"💸 Sell", key=f"sell_btn_{stock['symbol']}"):
                        if sell_qty > 0:
                            with st.spinner(f"Selling {sell_qty} shares of {stock['symbol']}..."):
                                res = call_backend(
                                    "/portfolio/sell", 
                                    method="POST",
                                    data={
                                        "ticker": stock["symbol"], 
                                        "shares": sell_qty, 
                                        "price": stock["current_price"]
                                    }
                                )
                                if res:
                                    st.success(f"✅ Sold {sell_qty} shares of {stock['symbol']}")
                                    st.rerun()
                        else:
                            st.warning("Enter a valid quantity to sell.")

# ----------------------------------
# Footer
# ----------------------------------
st.markdown("---")
st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")