# backend/langchain_core/utils/tools_config.py
"""
Central tool configuration: expose tools that accept a single input argument
(so they work with ZeroShotAgent). Wrapper funcs accept:
 - None -> treated as empty
 - dict  -> passed through
 - str   -> try to parse JSON, else treated as raw string (e.g., "AAPL" or '"AAPL"')
"""

import json
import logging
from typing import Any, Dict, Optional

from langchain.tools import Tool
from pydantic.v1 import BaseModel, Field

import requests

logger = logging.getLogger(__name__)
API_BASE = "http://localhost:8001/api"

# -------------------------
# Core (structured) helper functions (can be reused elsewhere)
# -------------------------
def get_stock_news(symbol: str) -> str:
    try:
        response = requests.get(f"{API_BASE}/news/{symbol}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data.get("news"):
            return f"No news found for {symbol}"
        news_list = []
        for article in data["news"][:5]:
            news_list.append(
                f"• {article.get('title')}\n  {article.get('publisher')} - {article.get('providerPublishTime')}\n  {article.get('link')}"
            )
        return f"Latest news for {symbol}:\n\n" + "\n\n".join(news_list)
    except Exception as e:
        logger.exception("Error fetching news:")
        return f"Error fetching news for {symbol}: {str(e)}"

def get_portfolio_value() -> str:
    try:
        response = requests.get(f"{API_BASE}/portfolio/value", timeout=10)
        response.raise_for_status()
        data = response.json()
        return (
            f"Portfolio Summary:\n"
            f"• Total Value: ${data.get('total_value', 0):,.2f}\n"
            f"• Cash Balance: ${data.get('cash_balance', 0):,.2f}\n"
            f"• Invested: ${data.get('invested_value', 0):,.2f}\n"
            f"• P&L: ${data.get('total_pnl', 0):,.2f} ({data.get('pnl_percent', 0):.2f}%)"
        )
    except Exception as e:
        logger.exception("Error fetching portfolio value:")
        return f"Error fetching portfolio value: {str(e)}"

def get_portfolio_holdings() -> str:
    try:
        response = requests.get(f"{API_BASE}/portfolio/holdings", timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data.get("holdings"):
            return "Portfolio is empty"
        holdings_list = []
        for stock in data["holdings"]:
            holdings_list.append(
                f"• {stock.get('symbol')}: {stock.get('quantity')} shares @ ${stock.get('current_price',0):.2f}\n"
                f"  Market Value: ${stock.get('market_value',0):,.2f} | P&L: ${stock.get('pnl',0):,.2f} ({stock.get('pnl_percent',0):.2f}%)"
            )
        return "Current Holdings:\n\n" + "\n\n".join(holdings_list)
    except Exception as e:
        logger.exception("Error fetching holdings:")
        return f"Error fetching holdings: {str(e)}"

def add_stock_to_portfolio(ticker: str, shares: float, price: float) -> str:
    try:
        resp = requests.post(
            f"{API_BASE}/portfolio/add",
            json={"ticker": ticker, "shares": shares, "price": price},
            timeout=10,
        )
        resp.raise_for_status()
        return f"✅ Successfully added {shares} shares of {ticker} at ${price:.2f}"
    except Exception as e:
        logger.exception("Error adding stock:")
        return f"Error adding stock: {str(e)}"

def predict_stock_price(symbol: str) -> str:
    try:
        response = requests.get(f"{API_BASE}/predict/{symbol}", timeout=30)
        response.raise_for_status()
        data = response.json()
        predictions = data.get("predictions", [])
        if not predictions:
            return f"No prediction available for {symbol}"
        current = float(data.get("current_price", 0) or 0)
        future = float(predictions[-1])
        change = ((future - current) / current) * 100 if current else 0.0
        return (
            f"Price Prediction for {symbol}:\n"
            f"• Current Price: ${current:.2f}\n"
            f"• Predicted Price: ${future:.2f}\n"
            f"• Expected Change: {change:+.2f}%\n"
            f"• Forecast Period: {len(predictions)} days"
        )
    except Exception as e:
        logger.exception("Error predicting stock:")
        return f"Error predicting stock price: {str(e)}"

# -------------------------
# Generic single-arg parser for agent-compatible Tools
# -------------------------
def _parse_single_arg(arg: Any) -> Optional[Any]:
    """
    Normalize agent-provided argument into python types:
    - None -> None
    - dict -> dict
    - str -> try json.loads, else return raw string
    """
    if arg is None:
        return None
    if isinstance(arg, dict):
        return arg
    if isinstance(arg, str):
        s = arg.strip()
        if s == "":
            return None
        # try to parse JSON
        try:
            return json.loads(s)
        except Exception:
            # not JSON, return raw string (e.g. 'AAPL' or '"AAPL"')
            # If the string is a quoted JSON string like '"AAPL"', json.loads would have worked.
            return s
    return arg

# -------------------------
# Wrapper functions that accept a single argument (for ZeroShotAgent)
# -------------------------
def _stock_news_wrapper(arg: Any) -> str:
    norm = _parse_single_arg(arg)
    # Accept either: {"symbol":"AAPL"}  or "AAPL"  or '"AAPL"'
    symbol = None
    if isinstance(norm, dict):
        symbol = norm.get("symbol") or norm.get("ticker")
    elif isinstance(norm, str):
        symbol = norm
    if symbol is None:
        return "Error: missing symbol. Provide 'AAPL' or {\"symbol\":\"AAPL\"}."
    return get_stock_news(symbol.upper())

def _portfolio_value_wrapper(arg: Any) -> str:
    # ignore arg
    return get_portfolio_value()

def _portfolio_holdings_wrapper(arg: Any) -> str:
    # ignore arg
    return get_portfolio_holdings()

def _add_stock_wrapper(arg: Any) -> str:
    norm = _parse_single_arg(arg)
    if isinstance(norm, dict):
        ticker = norm.get("ticker") or norm.get("symbol")
        shares = norm.get("shares")
        price = norm.get("price")
    elif isinstance(norm, str):
        # allow quick string: "AAPL,10,150"
        parts = [p.strip() for p in norm.split(",")]
        if len(parts) >= 3:
            ticker, shares_s, price_s = parts[0], parts[1], parts[2]
            try:
                shares = float(shares_s)
                price = float(price_s)
            except Exception:
                return "Error: could not parse shares or price. Use {\"ticker\":\"AAPL\",\"shares\":10,\"price\":150} or 'AAPL,10,150'."
        else:
            return "Error: AddStock input must be JSON or 'TICKER,shares,price'."
    else:
        return "Error: invalid input for AddStockTool."

    if not ticker or shares is None or price is None:
        return "Error: missing fields. Provide {\"ticker\":\"AAPL\",\"shares\":10,\"price\":150}."
    return add_stock_to_portfolio(ticker.upper(), float(shares), float(price))

def _stock_prediction_wrapper(arg: Any) -> str:
    norm = _parse_single_arg(arg)
    symbol = None
    if isinstance(norm, dict):
        symbol = norm.get("symbol")
    elif isinstance(norm, str):
        symbol = norm
    if not symbol:
        return "Error: missing symbol for prediction. Provide 'AAPL' or {\"symbol\":\"AAPL\"}."
    return predict_stock_price(symbol.upper())

# -------------------------
# Export tools as single-arg LangChain Tool objects
# -------------------------
tools = [
    Tool(
        name="StockNewsTool",
        func=_stock_news_wrapper,
        description='Fetch latest news for a stock. Input: "AAPL" or {"symbol":"AAPL"} (single-arg).',
    ),
    Tool(
        name="PortfolioValueTool",
        func=_portfolio_value_wrapper,
        description="Get portfolio summary. Input: {} or no input (single-arg ignored).",
    ),
    Tool(
        name="PortfolioHoldingsTool",
        func=_portfolio_holdings_wrapper,
        description="Get portfolio holdings. Input: {} or no input (single-arg ignored).",
    ),
    Tool(
        name="AddStockTool",
        func=_add_stock_wrapper,
        description='Add stock to portfolio. Input: {"ticker":"AAPL","shares":10,"price":150} OR "AAPL,10,150".',
    ),
    Tool(
        name="StockPredictionTool",
        func=_stock_prediction_wrapper,
        description='Predict stock price. Input: "AAPL" or {"symbol":"AAPL"}.',
    ),
]