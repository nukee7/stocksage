# backend/langchain_core/agent.py

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

def get_agent_response(prompt: str) -> str:
    """Handles chat interaction with the LLM."""
    system_message = SystemMessage(content="You are StockSage, an AI financial assistant.")
    human_message = HumanMessage(content=prompt)

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    response = model.invoke([system_message, human_message])
    return response.content