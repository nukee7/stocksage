# services/chatbot_service.py

from agents.agent import run_agent

def handle_user_query(query: str):
    """
    Handles user input and gets the LangChain agent response.
    """
    response = run_agent(query)
    return response