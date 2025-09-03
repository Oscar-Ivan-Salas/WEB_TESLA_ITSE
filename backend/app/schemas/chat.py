"""
Chat-related Pydantic schemas for the Tesla CRM application.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from .base import BaseSchema

class MessageBase(BaseModel):
    """Base message schema with common fields."""
    content: str = Field(..., description="The message content")
    sender: str = Field(..., description="The sender of the message (user or assistant)")
    message_type: str = Field("text", description="Type of the message (text, image, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata for the message"
    )

class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    conversation_id: Optional[int] = Field(
        None,
        description="ID of the conversation this message belongs to"
    )

class MessageUpdate(BaseModel):
    """Schema for updating a message."""
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class Message(MessageBase, BaseSchema):
    """Complete message schema including database fields."""
    conversation_id: Optional[int] = None
    is_read: bool = False

    class Config:
        orm_mode = True

class ConversationBase(BaseModel):
    """Base conversation schema."""
    title: Optional[str] = Field(
        None,
        description="Title or subject of the conversation"
    )
    status: str = Field(
        "active",
        description="Status of the conversation (active, closed, pending, etc.)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata for the conversation"
    )

class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""
    lead_id: Optional[int] = Field(
        None,
        description="ID of the lead associated with this conversation"
    )

class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class Conversation(ConversationBase, BaseSchema):
    """Complete conversation schema including related messages."""
    lead_id: Optional[int] = None
    messages: List[Message] = []

    class Config:
        orm_mode = True

class ChatResponse(BaseModel):
    """Response schema for chat interactions."""
    message: Message
    conversation: Optional[Conversation] = None
    suggested_responses: Optional[List[str]] = Field(
        None,
        description="List of suggested responses for the user"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata for the response"
    )
