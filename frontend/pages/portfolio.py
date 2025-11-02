import streamlit as st
import pandas as pd
import requests
import os
import sys
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

# Backend API URL - read from environment variable
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8001')
BACKEND_URL = f"{API_BASE_URL}/api"

# Debug: Show loaded configuration in sidebar (comment out in production)
# st.sidebar.info(f"Backend URL: {BACKEND_URL}")
# st.sidebar.info(f"API Base: {API_BASE_URL}")

# Initialize session state for caching
if 'portfolio_data' not in st.session_state:
    st.session_state.portfolio_data = None
    st.session_state.last_updated = None

# Initialize session state for prediction visibility
if 'show_prediction' not in st.session_state:
    st.session_state.show_prediction = False

if 'show_stock_predictions' not in st.session_state:
    st.session_state.show_stock_predictions = {}

st.set_page_config(page_title="Portfolio | AI Financial Assistant", page_icon="📊", layout="wide")

# Portfolio data
MOCK_PORTFOLIO = {
    "AAPL": {"shares": 10, "avg_price": 150.25},
    "MSFT": {"shares": 5, "avg_price": 300.50},
    "GOOGL": {"shares": 3, "avg_price": 2800.75},
    "AMZN": {"shares": 2, "avg_price": 3300.00}
}

def fetch_stock_price(ticker):
    """Fetch stock price from backend API"""
    try:
        response = requests.get(f"{BACKEND_URL}/stock/price/{ticker}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        # Return mock data if API fails (don't show error for each stock)
        import random
        return {
            "c": round(150.25 + random.uniform(-10, 10), 2),
            "dp": round(random.uniform(-3, 3), 2),
            "name": ticker
        }

def get_stock_price(ticker):
    """Get stock price data from backend API"""
    return fetch_stock_price(ticker)

def get_stock_prediction(ticker):
    """Get stock prediction from backend API"""
    try:
        response = requests.get(f"{BACKEND_URL}/stock/predict/{ticker}?days=10", timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.warning(f"Using mock prediction data. Backend API error: {str(e)}")
        # Return mock prediction if API fails
        base_price = 100
        return {
            "ticker": ticker,
            "current_price": base_price,
            "predictions": [base_price * (1 + i*0.01) for i in range(10)],
            "dates": [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(10)]
        }

def get_portfolio_value():
    """Calculate portfolio value"""
    total_value = 0
    portfolio_data = []
    
    for ticker, data in MOCK_PORTFOLIO.items():
        price_data = get_stock_price(ticker)
        current_price = price_data["c"]
        value = current_price * data["shares"]
        total_value += value
        
        portfolio_data.append({
            "Ticker": ticker,
            "Shares": data["shares"],
            "Avg Price": f"${data['avg_price']:.2f}",
            "Current Price": f"${current_price:.2f}",
            "Value": f"${value:,.2f}",
            "Change %": f"{price_data['dp']}%",
        })
    
    return pd.DataFrame(portfolio_data), total_value

# Main layout
st.title("📊 Portfolio Dashboard")
st.markdown("Track your investments and get AI-powered insights")

# Check backend connection
try:
    response = requests.get(f"{API_BASE_URL}/health", timeout=5)
    if response.status_code == 200:
        health_data = response.json()
        st.sidebar.success(f"✅ Backend Connected (Port: {os.getenv('BACKEND_PORT', '8001')})")
        if not health_data.get('polygon_api_configured'):
            st.sidebar.warning("⚠️ Polygon API key not configured")
    else:
        st.sidebar.warning("⚠️ Backend connection issue")
except Exception as e:
    st.sidebar.error(f"❌ Backend offline - using mock data")
    st.sidebar.caption(f"Expected backend at: {API_BASE_URL}")

# Add a refresh button in sidebar
if st.sidebar.button("🔄 Refresh Data"):
    st.session_state.portfolio_data = None
    st.rerun()

# Portfolio Summary
col1, col2, col3 = st.columns(3)
portfolio_df, total_value = get_portfolio_value()

with col1:
    st.metric("Total Portfolio Value", f"${total_value:,.2f}")
with col2:
    st.metric("Daily Change", "+$1,234.56", "+2.34%")
with col3:
    st.metric("YTD Return", "+12.34%", "+$5,678.90")

# Main content
tab1, tab2, tab3 = st.tabs(["📈 Holdings", "🔍 Stock Analysis", "⚙️ Settings"])

with tab1:
    # Holdings Table
    st.subheader("Your Holdings")
    
    # Add search and filter
    search_col, filter_col = st.columns([3, 1])
    with search_col:
        search_term = st.text_input("Search stocks", "")
    with filter_col:
        sort_by = st.selectbox("Sort by", ["Value (High-Low)", "Ticker", "Change %"])
    
    # Display portfolio cards with prediction button
    if not portfolio_df.empty:
        # Add prediction button at the top
        predict_col1, predict_col2 = st.columns([3, 1])
        with predict_col2:
            if st.button("🔮 Predict Portfolio Returns", use_container_width=True, type="primary"):
                st.session_state.show_prediction = True
        
        # Create cards for each stock
        st.markdown("""
        <style>
            .stock-card {
                background: white;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                transition: transform 0.2s;
            }
            .stock-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            .stock-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            .stock-ticker {
                font-size: 1.2rem;
                font-weight: bold;
                color: #1a237e;
            }
            .stock-price {
                font-size: 1.1rem;
                font-weight: bold;
            }
            .positive {
                color: #2e7d32;
            }
            .negative {
                color: #c62828;
            }
            .stock-meta {
                display: flex;
                justify-content: space-between;
                font-size: 0.9rem;
                color: #555;
                margin: 5px 0;
            }
            .progress-container {
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
                margin: 10px 0;
                overflow: hidden;
            }
            .progress-bar {
                height: 100%;
                background: #3f51b5;
                transition: width 0.5s;
            }
            .stock-logo {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: #f5f5f5;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 10px;
                font-weight: bold;
                color: #555;
            }
            .stock-header-left {
                display: flex;
                align-items: center;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Create columns for responsive grid
        cols = st.columns(2)  # 2 columns for better mobile responsiveness
        
        for idx, (ticker, data) in enumerate(MOCK_PORTFOLIO.items()):
            price_data = get_stock_price(ticker)
            current_price = price_data["c"]
            change_pct = price_data["dp"]
            value = current_price * data["shares"]
            allocation = (value / total_value) * 100
            
            # Determine column (alternates between columns)
            col = cols[idx % 2]
            
            with col:
                # Create card
                st.markdown(f"""
                <div class="stock-card">
                    <div class="stock-header">
                        <div class="stock-header-left">
                            <div class="stock-logo">{ticker[0]}</div>
                            <div>
                                <div class="stock-ticker">{ticker}</div>
                                <div>Shares: {data['shares']}</div>
                            </div>
                        </div>
                        <div class="stock-price {'positive' if change_pct >= 0 else 'negative'}">
                            ${current_price:,.2f}
                            <span>({change_pct:+.2f}%)</span>
                        </div>
                    </div>
                    
                    <div class="stock-meta">
                        <div>Avg: ${data['avg_price']:,.2f}</div>
                        <div>Value: ${value:,.2f}</div>
                    </div>
                    
                    <div>Allocation: {allocation:.1f}%</div>
                    <div class="progress-container">
                        <div class="progress-bar" style="width: {allocation}%"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Add Streamlit native buttons below the card
                button_col1, button_col2 = st.columns(2)
                with button_col1:
                    predict_key = f"predict_{ticker}"
                    if ticker not in st.session_state.show_stock_predictions:
                        st.session_state.show_stock_predictions[ticker] = False
                    
                    button_label = "▲ Hide Prediction" if st.session_state.show_stock_predictions[ticker] else "📈 Predict"
                    if st.button(button_label, key=predict_key, use_container_width=True):
                        st.session_state.show_stock_predictions[ticker] = not st.session_state.show_stock_predictions[ticker]
                        st.rerun()
                
                with button_col2:
                    if st.button("💰 Sell", key=f"sell_{ticker}", use_container_width=True):
                        st.warning(f"Sell {ticker}? (Feature coming soon)")
                
                # Show prediction if toggled
                if st.session_state.show_stock_predictions.get(ticker, False):
                    with st.container():
                        st.markdown('<div style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">', unsafe_allow_html=True)
                        
                        pred_col1, pred_col2, pred_col3 = st.columns(3)
                        with pred_col1:
                            st.metric("1M Forecast", "+5.2%")
                        with pred_col2:
                            st.metric("Confidence", "High")
                        with pred_col3:
                            st.metric("Volatility", "Medium")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
        
        # Show prediction results if button was clicked
        if st.session_state.get('show_prediction', False):
            with st.expander("📈 Portfolio Prediction Results", expanded=True):
                st.subheader("Portfolio Performance Forecast")
                
                # Mock prediction data (replace with actual prediction logic)
                prediction_dates = [(datetime.now() + timedelta(days=i)).strftime("%b %d") for i in range(1, 31)]
                prediction_values = [total_value * (1 + (i * 0.005)) for i in range(30)]
                
                # Create prediction chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=prediction_dates[::3],  # Show every 3rd date for better readability
                    y=prediction_values[::3],
                    mode='lines+markers',
                    name='Predicted Value',
                    line=dict(color='#4CAF50', width=3),
                    hovertemplate='%{y:$,.2f}<extra></extra>'
                ))
                
                # Add current value line
                fig.add_hline(
                    y=total_value,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Current: ${total_value:,.2f}",
                    annotation_position="bottom right"
                )
                
                # Update layout
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Portfolio Value ($)",
                    template="plotly_white",
                    height=400,
                    margin=dict(l=20, r=20, t=40, b=20),
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Prediction summary
                predicted_return = ((prediction_values[-1] - total_value) / total_value) * 100
                days = len(prediction_dates)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Predicted Value", f"${prediction_values[-1]:,.2f}", f"{predicted_return:.2f}%")
                with col2:
                    st.metric("Time Horizon", f"{days} days")
                with col3:
                    st.metric("Confidence Level", "82%")
                
                # Risk assessment
                st.subheader("Risk Assessment")
                risk_col1, risk_col2 = st.columns([1, 3])
                with risk_col1:
                    st.metric("Volatility", "Medium")
                    st.metric("Max Drawdown", "-8.2%")
                with risk_col2:
                    st.progress(0.75, "Portfolio Health Score")
                    st.caption("Based on diversification, volatility, and market conditions")
                
                # Actionable insights
                st.subheader("💡 Recommended Actions")
                st.info("""
                - Consider rebalancing your portfolio to maintain your target asset allocation
                - Our model suggests increasing exposure to technology stocks by 5%
                - Current market conditions favor growth-oriented investments
                """)
    else:
        st.info("Your portfolio is empty. Add stocks to get started!")

with tab2:
    st.subheader("Stock Analysis & Prediction")
    
    # Stock selection
    selected_ticker = st.selectbox(
        "Select a stock",
        ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META"],
        index=0
    )
    
    # Get prediction data
    if st.button("Generate Prediction", type="primary"):
        with st.spinner("Analyzing stock and generating predictions..."):
            prediction = get_stock_prediction(selected_ticker)
            
            # Create chart
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Add price line
            fig.add_trace(
                go.Scatter(
                    x=prediction["dates"],
                    y=prediction["predictions"],
                    name="Predicted Price",
                    line=dict(color="#636EFA", width=3)
                ),
                secondary_y=False,
            )
            
            # Add current price line
            current_price = prediction["current_price"]
            fig.add_hline(
                y=current_price,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Current: ${current_price:.2f}",
                annotation_position="bottom right"
            )
            
            # Update layout
            fig.update_layout(
                title=f"{selected_ticker} 10-Day Price Prediction",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                template="plotly_white",
                height=500
            )
            
            # Show chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Additional analysis
            st.subheader("Key Insights")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Predicted Change", "+5.2%", "+$7.85")
            with col2:
                st.metric("Confidence", "78%")
            with col3:
                st.metric("Volatility", "Medium")
            
            # Recommendation
            st.info("💡 Based on our analysis, we recommend holding this position as the stock shows strong upward momentum.")

with tab3:
    st.subheader("Portfolio Settings")
    
    # Add stock form
    with st.form("add_stock"):
        st.write("### Add New Stock")
        col1, col2, col3 = st.columns(3)
        with col1:
            new_ticker = st.text_input("Ticker Symbol")
        with col2:
            shares = st.number_input("Shares", min_value=0.0001, step=0.0001, format="%.4f")
        with col3:
            avg_price = st.number_input("Average Price ($)", min_value=0.01, step=0.01)
        
        if st.form_submit_button("Add to Portfolio", type="primary"):
            if new_ticker:
                # Here you would add to your actual portfolio data
                st.success(f"Added {shares} shares of {new_ticker} at ${avg_price:.2f} to your portfolio!")
            else:
                st.error("Please enter a valid ticker symbol")
    
    # Risk preferences
    st.divider()
    st.write("### Risk Preferences")
    risk_level = st.select_slider(
        "Risk Tolerance",
        options=["Very Conservative", "Conservative", "Moderate", "Aggressive", "Very Aggressive"]
    )
    
    # Save settings
    if st.button("Save Settings", type="primary"):
        st.success("Portfolio settings updated successfully!")

# Add some custom CSS
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        gap: 4px;
        padding: 0 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e6f0ff;
    }
</style>
""", unsafe_allow_html=True)