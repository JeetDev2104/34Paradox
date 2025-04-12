from fastapi import APIRouter, HTTPException
from typing import Dict
from services.chatbot import chatbot_service
from pydantic import BaseModel

router = APIRouter()

class ChatQuery(BaseModel):
    query: str

@router.post("/query", response_model=Dict)
async def process_chat_query(chat_query: ChatQuery):
    """Process a chat query and return relevant information"""
    try:
        response = await chatbot_service.process_query(chat_query.query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 