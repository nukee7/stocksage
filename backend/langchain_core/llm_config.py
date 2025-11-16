import os
from langchain.chat_models import ChatOpenAI

def load_llm():
    """Centralized LLM configuration (e.g., GPT-4, local LLM)."""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set in environment")

    llm = ChatOpenAI(
        model="gpt-4-turbo",
        temperature=0.4,
        openai_api_key=OPENAI_API_KEY
    )
    return llm
