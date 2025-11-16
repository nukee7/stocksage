# backend/langchain_core/utils/agent_builder.py
import logging
from langchain.agents import initialize_agent, AgentType
from backend.langchain_core.utils.llm_loader import GroqLLM
from backend.langchain_core.utils.tools_config import tools

logger = logging.getLogger(__name__)


def create_agent(only_news: bool = True):
    """
    Create and return a simple agent configured for the current LangChain version.

    Behavior:
      - By default (only_news=True) the agent only sees the StockNewsTool so it won't
        attempt to call AddStockTool or other multi-purpose tools.
      - Uses ZERO_SHOT_REACT_DESCRIPTION for straightforward tool usage.
      - Keeps verbosity enabled to help debugging during development.
    """

    llm = GroqLLM()  # your Groq-backed LLM wrapper

    # Optionally restrict tools to StockNewsTool only (simple & safe for news use-cases)
    if only_news:
        allowed = [t for t in tools if t.name == "StockNewsTool"]
        logger.info("Agent tools (whitelisted): %s", [t.name for t in allowed])
        use_tools = allowed
    else:
        logger.info("Agent tools (all): %s", [t.name for t in tools])
        use_tools = tools

    agent_executor = initialize_agent(
        tools=use_tools,
        llm=llm,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
    )

    return agent_executor


# Convenience instance (whitelist StockNewsTool by default)
agent = create_agent()