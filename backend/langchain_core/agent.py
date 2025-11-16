from langchain.agents import initialize_agent
from langchain_core.llm_config import load_llm
from langchain_core.memory import get_memory
from langchain_core.tools.portfolio_tools import (
    PortfolioValueTool,
    PortfolioHoldingsTool,
    AddStockTool
)
from langchain_core.tools.stock_tools import StockPredictionTool
from langchain_core.tools.news_tools import StockNewsTool

def create_agent():
    """Initialize LangChain agent with all tools and memory."""
    llm = load_llm()
    memory = get_memory()

    tools = [
        StockPredictionTool,
        StockNewsTool,
        PortfolioValueTool,
        PortfolioHoldingsTool,
        AddStockTool
    ]

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent_type="chat-conversational-react-description",
        memory=memory,
        verbose=True,
    )
    return agent
