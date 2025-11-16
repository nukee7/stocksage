import asyncio
from langchain.agents import Tool
from backend.service.portfolio_service import (
    get_portfolio_value_service,
    get_portfolio_holdings_service,
    add_stock_service
)

async def _portfolio_value():
    return await get_portfolio_value_service()

async def _portfolio_holdings():
    return await get_portfolio_holdings_service()

async def _add_stock(ticker: str, shares: float, price: float):
    return await add_stock_service(ticker, shares, price)

PortfolioValueTool = Tool(
    name="PortfolioValueTool",
    func=lambda _: asyncio.run(_portfolio_value()),
    description="Get total portfolio performance summary."
)

PortfolioHoldingsTool = Tool(
    name="PortfolioHoldingsTool",
    func=lambda _: asyncio.run(_portfolio_holdings()),
    description="List all holdings currently in the portfolio."
)

AddStockTool = Tool(
    name="AddStockTool",
    func=lambda x: asyncio.run(_add_stock(**x)),
    description="Add a stock to your portfolio. Requires ticker, shares, and price."
)
