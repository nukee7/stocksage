from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.service.chatbot_service import run_chatbot

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

class ChatRequest(BaseModel):
    message: str

@router.post("/query")
async def chatbot_query(req: ChatRequest):
    try:
        response = await run_chatbot(req.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))