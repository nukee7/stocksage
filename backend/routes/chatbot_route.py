# routes/chatbot_routes.py

from fastapi import APIRouter
from pydantic import BaseModel
from service.chatbot_service import handle_user_query

router = APIRouter(prefix="/chat", tags=["Chatbot"])

class ChatRequest(BaseModel):
    query: str

@router.post("/")
async def chat_with_agent(request: ChatRequest):
    """
    Route for interacting with the AI chatbot.
    """
    response = handle_user_query(request.query)
    return {"response": response}