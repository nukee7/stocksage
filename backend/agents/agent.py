# agents/agent.py
# --------------------------------------------------------------
#  LangChain ≥ 1.0.3  –  ReAct agent (CORRECT IMPORT)
# --------------------------------------------------------------

from typing import List
from langchain_openai import ChatOpenAI
from langchain import agents
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import StructuredTool
from langchain.agents import AgentExecutor

# Import your custom tools
from agents.tools.stock_tools import (
    get_stock_prediction,
    get_stock_sentiment,
    get_portfolio_advice,
)

# ------------------------------------------------------------------
# 1. Define tools
# ------------------------------------------------------------------
tools: List[StructuredTool] = [
    StructuredTool.from_function(
        func=get_stock_prediction,
        name="StockPrediction",
        description="Predicts next 10-day prices for a ticker using LSTM+XGBoost. Input: ticker (str).",
    ),
    StructuredTool.from_function(
        func=get_stock_sentiment,
        name="StockSentiment",
        description="Gets latest news sentiment score (-1 to +1) for a ticker. Input: ticker (str).",
    ),
    StructuredTool.from_function(
        func=get_portfolio_advice,
        name="PortfolioAdvisor",
        description="Gives rebalancing advice. Input: JSON string of {'ticker': weight}.",
    ),
]

# ------------------------------------------------------------------
# 2. LLM
# ------------------------------------------------------------------
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)

# ------------------------------------------------------------------
# 3. Prompt
# ------------------------------------------------------------------
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a financial assistant. Use tools to answer. Return only the final answer.",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# ------------------------------------------------------------------
# 4. Create ReAct agent (CORRECT WAY)
# ------------------------------------------------------------------
react_agent = agents.create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt,
)

# ------------------------------------------------------------------
# 5. Agent executor
# ------------------------------------------------------------------
agent_executor = AgentExecutor(
    agent=react_agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)

# ------------------------------------------------------------------
# 6. Run function
# ------------------------------------------------------------------
def run_agent(user_query: str, chat_history: List = None) -> str:
    if chat_history is None:
        chat_history = []

    try:
        result = agent_executor.invoke(
            {
                "input": user_query,
                "chat_history": chat_history,
            }
        )
        return result["output"]
    except Exception as e:
        return f"Error: {str(e)}"