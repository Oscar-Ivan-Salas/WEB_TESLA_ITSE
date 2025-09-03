"""
Chat service for handling chat-related business logic.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models import Conversation, Message, Lead
from app.schemas.chat import (
    MessageCreate, MessageUpdate, ConversationCreate, 
    ConversationUpdate, ChatResponse
)

class ChatService:
    """Service class for chat-related operations."""
    
    @staticmethod
    async def create_conversation(
        db: Session, 
        conversation_in: ConversationCreate
    ) -> Conversation:
        """Create a new conversation."""
        db_conversation = Conversation(
            **conversation_in.dict(exclude={"lead_id"}, exclude_unset=True)
        )
        
        if conversation_in.lead_id:
            # Verify the lead exists
            lead = db.query(Lead).filter(Lead.id == conversation_in.lead_id).first()
            if not lead:
                raise ValueError("Lead not found")
            db_conversation.lead_id = conversation_in.lead_id
        
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        return db_conversation
    
    @staticmethod
    async def get_conversation(
        db: Session, 
        conversation_id: int
    ) -> Optional[Conversation]:
        """Get a conversation by ID."""
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    @staticmethod
    async def get_conversations(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        lead_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[Conversation]:
        """Get a list of conversations with optional filtering."""
        query = db.query(Conversation)
        
        if lead_id is not None:
            query = query.filter(Conversation.lead_id == lead_id)
        
        if status:
            query = query.filter(Conversation.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    async def update_conversation(
        db: Session,
        conversation_id: int,
        conversation_in: ConversationUpdate,
    ) -> Optional[Conversation]:
        """Update a conversation."""
        db_conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not db_conversation:
            return None
        
        update_data = conversation_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_conversation, field, value)
        
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        return db_conversation
    
    @staticmethod
    async def create_message(
        db: Session,
        message_in: MessageCreate,
    ) -> Message:
        """Create a new message in a conversation."""
        # Verify the conversation exists
        conversation = db.query(Conversation).filter(
            Conversation.id == message_in.conversation_id
        ).first()
        
        if not conversation:
            raise ValueError("Conversation not found")
        
        db_message = Message(**message_in.dict())
        db.add(db_message)
        
        # Update conversation's updated_at timestamp
        conversation.updated_at = datetime.utcnow()
        db.add(conversation)
        
        db.commit()
        db.refresh(db_message)
        return db_message
    
    @staticmethod
    async def get_messages(
        db: Session,
        conversation_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Message]:
        """Get messages in a conversation."""
        return (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    @staticmethod
    async def process_message(
        db: Session,
        message_in: MessageCreate,
        use_ai: bool = True,
    ) -> ChatResponse:
        """
        Process an incoming message and generate a response.
        
        This is the main chat endpoint that handles both user messages and AI responses.
        """
        from app.ai.chatbot import RuleBasedChatbot
        
        # Create or get conversation
        if not message_in.conversation_id:
            # Create a new conversation if no conversation_id is provided
            conversation = Conversation()
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            message_in.conversation_id = conversation.id
        else:
            # Verify the conversation exists
            conversation = await ChatService.get_conversation(
                db, message_in.conversation_id
            )
            if not conversation:
                raise ValueError("Conversation not found")
        
        # Save the user's message
        user_message = await ChatService.create_message(db, message_in)
        
        # Generate response
        if use_ai:
            chatbot = RuleBasedChatbot()
            ai_response = chatbot.generate_response(message_in.content)
            
            # Save the AI's response
            ai_message = MessageCreate(
                content=ai_response,
                sender="assistant",
                conversation_id=conversation.id,
                message_type="text"
            )
            
            saved_ai_message = await ChatService.create_message(db, ai_message)
        else:
            ai_response = "AI responses are currently disabled."
            saved_ai_message = None
        
        # Get suggested responses
        suggested_responses = await ChatService.get_suggested_responses(
            db, conversation.id
        )
        
        return ChatResponse(
            message=saved_ai_message or user_message,
            conversation=conversation,
            suggested_responses=suggested_responses
        )
    
    @staticmethod
    async def get_suggested_responses(
        db: Session,
        conversation_id: int,
        limit: int = 5,
    ) -> List[str]:
        """
        Get suggested responses for a conversation.
        
        This is a simple implementation that returns predefined suggestions.
        In a real application, this could use more sophisticated logic.
        """
        # This is a simple implementation - in a real app, you might use:
        # 1. A rule-based system
        # 2. Machine learning model
        # 3. Or a combination of both
        
        return [
            "¿Podría proporcionar más detalles?",
            "Entendido, ¿en qué más puedo ayudarte?",
            "¿Te gustaría que te llame para discutir esto?",
            "¿Tienes alguna otra pregunta?",
            "¿Necesitas ayuda con algo más?"
        ][:limit]

# Create a singleton instance
chat_service = ChatService()
