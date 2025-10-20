"""Chat API endpoints."""

from fastapi import APIRouter, HTTPException

from app.core.logging import logger
from app.models.chat import ChatRequest, ChatResponse
from app.services.ai.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a chat message and return AI response.
    
    The AI can:
    - Answer questions about GW2 builds and meta
    - Parse GW2Skill links
    - Suggest team compositions
    - Provide build recommendations
    """
    try:
        logger.info(f"Processing chat message: {request.message[:50]}...")
        response = await chat_service.process_message(request)
        return response
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")
