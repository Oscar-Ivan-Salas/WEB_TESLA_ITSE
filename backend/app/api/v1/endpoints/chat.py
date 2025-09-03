"""
Chat API endpoints for the Tesla CRM application.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.chat import (
    Message, MessageCreate, MessageUpdate,
    Conversation, ConversationCreate, ConversationUpdate, ChatResponse
)
from app.database import get_db
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/conversations/", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new conversation.
    
    - If lead_id is provided, associates the conversation with an existing lead.
    - If lead_id is not provided, creates a new lead with the provided information.
    """
    try:
        return await chat_service.create_conversation(db, conversation)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/conversations/", response_model=List[Conversation])
async def list_conversations(
    skip: int = 0,
    limit: int = 100,
    lead_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all conversations with optional filtering.
    """
    return await chat_service.get_conversations(
        db, skip=skip, limit=limit, lead_id=lead_id, status=status
    )

@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific conversation by ID.
    """
    conversation = await chat_service.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return conversation

@router.put("/conversations/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: int,
    conversation_update: ConversationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a conversation's information.
    """
    updated = await chat_service.update_conversation(
        db, conversation_id, conversation_update
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return updated

@router.post("/messages/", response_model=Message, status_code=status.HTTP_201_CREATED)
async def create_message(
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    """
    Send a new message in a conversation.
    """
    try:
        return await chat_service.create_message(db, message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/conversations/{conversation_id}/messages", response_model=List[Message])
async def get_conversation_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all messages in a conversation.
    """
    return await chat_service.get_messages(
        db, conversation_id=conversation_id, skip=skip, limit=limit
    )

@router.post("/send-message/", response_model=ChatResponse)
async def send_message(
    message: MessageCreate,
    use_ai: bool = True,
    db: Session = Depends(get_db)
):
    """
    Send a message and get a response.
    
    This is the main chat endpoint that handles both user messages and AI responses.
    """
    try:
        return await chat_service.process_message(db, message, use_ai=use_ai)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/suggested-responses/", response_model=List[str])
async def get_suggested_responses(
    conversation_id: int,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Get suggested responses for a conversation.
    """
    try:
        return await chat_service.get_suggested_responses(
            db, conversation_id, limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
