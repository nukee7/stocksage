from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.orchestrator import run_chatbot

router = APIRouter()

class ChatRequest(BaseModel):
    query: str

@router.post("/chatbot")
async def chatbot_route(request: ChatRequest):
    try:
        response = await run_chatbot(request.query)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {e}")
