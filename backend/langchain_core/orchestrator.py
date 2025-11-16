import asyncio
from langchain_core.agent import create_agent

# Initialize globally (warm agent)
_agent = create_agent()

async def run_chatbot(query: str) -> str:
    """Run user query through the LangChain agent."""
    if not query.strip():
        return "Please enter a valid question."

    try:
        response = await asyncio.to_thread(_agent.run, query)
        return response
    except Exception as e:
        return f"❌ Error: {str(e)}"
