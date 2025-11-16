# backend/langchain_core/tools/portfolio_tools.py
import asyncio
from backend.service.portfolio_service import (
    get_portfolio_value_service,
    get_portfolio_holdings_service,
    add_stock_service
)

# keep raw async functions, but expose sync-callable wrappers through tools_config
async def _portfolio_value():
    # returns dict/string summarizing portfolio value
    return await get_portfolio_value_service()

async def _portfolio_holdings():
    return await get_portfolio_holdings_service()

async def _add_stock(ticker: str, shares: float, price: float):
    return await add_stock_service(ticker, shares, price)


# NOTE: the tools_config wrapper will call these via asyncio.run and will pass normalized inputs.
# These implementations should return JSON-serializable results (dict/list/str).