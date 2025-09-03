"""
Conversation and Message models for the Tesla CRM application.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum, JSON, DateTime, Boolean
from sqlalchemy.orm import relationship

from .base import Base

class Conversation(Base):
    """
    A conversation represents a thread of messages between a user and the system.
    It can be associated with a lead.
    """
    __tablename__ = "conversations"
    
    # Basic Information
    title = Column(String(200), nullable=True, index=True)
    
    # Status
    status = Column(
        String(50),
        default="active",
        nullable=False,
        index=True,
        comment="Status of the conversation (active, closed, pending, etc.)"
    )
    
    # Relationships
    lead_id = Column(
        Integer,
        ForeignKey('leads.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    
    # Metadata
    metadata_ = Column('metadata', JSON, default=dict, nullable=False)
    
    # Relationships
    lead = relationship("Lead", back_populates="conversations")
    messages = relationship(
        "Message", 
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at.asc()"
    )
    
    def __repr__(self):
        return f"<Conversation {self.id} - {self.title or 'Untitled'}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary with proper type handling."""
        result = super().to_dict()
        
        # Handle metadata
        if 'metadata_' in result:
            result['metadata'] = result.pop('metadata_')
            
        # Include messages if loaded
        if self.messages:
            result['messages'] = [msg.to_dict() for msg in self.messages]
            
        return result


class Message(Base):
    """
    A message in a conversation.
    """
    __tablename__ = "messages"
    
    # Message Content
    content = Column(Text, nullable=False)
    
    # Sender Information
    sender = Column(
        String(50),
        nullable=False,
        index=True,
        comment="The sender of the message (user, assistant, system, etc.)"
    )
    
    # Message Type
    message_type = Column(
        String(50),
        default="text",
        nullable=False,
        comment="Type of message (text, image, file, etc.)"
    )
    
    # Status
    is_read = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether the message has been read by the recipient"
    )
    
    # Relationships
    conversation_id = Column(
        Integer,
        ForeignKey('conversations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Metadata
    metadata_ = Column('metadata', JSON, default=dict, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message {self.id} from {self.sender}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary with proper type handling."""
        result = super().to_dict()
        
        # Handle metadata
        if 'metadata_' in result:
            result['metadata'] = result.pop('metadata_')
            
        return result
