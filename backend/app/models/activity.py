"""
Activity Log model for tracking user and system activities.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base import Base

class ActivityLog(Base):
    """
    Activity log for tracking user actions and system events.
    """
    __tablename__ = "activity_logs"
    
    # Action information
    action = Column(
        String(100),
        nullable=False,
        index=True,
        comment="The action performed (e.g., 'user.login', 'lead.created')"
    )
    
    # Entity information
    entity_type = Column(
        String(50),
        nullable=True,
        index=True,
        comment="Type of entity this activity is related to (e.g., 'lead', 'conversation')"
    )
    
    entity_id = Column(
        Integer,
        nullable=True,
        index=True,
        comment="ID of the entity this activity is related to"
    )
    
    # User who performed the action (if any)
    user_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Additional details
    ip_address = Column(
        String(50),
        nullable=True,
        comment="IP address of the user who performed the action"
    )
    
    user_agent = Column(
        Text,
        nullable=True,
        comment="User agent string of the client"
    )
    
    details = Column(
        JSON,
        nullable=True,
        comment="Additional details about the activity in JSON format"
    )
    
    # Indexes for common query patterns
    __table_args__ = (
        # Composite index for querying by entity
        Index('ix_activity_logs_entity', 'entity_type', 'entity_id'),
        # Index for querying by user and time
        Index('ix_activity_logs_user_time', 'user_id', 'created_at'),
        # Index for querying by action and time
        Index('ix_activity_logs_action_time', 'action', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ActivityLog {self.action} by {self.user_id or 'system'}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert activity log to dictionary with proper type handling."""
        result = super().to_dict()
        
        # Handle details JSON
        if 'details' in result and result['details'] is None:
            result['details'] = {}
            
        return result
    
    @classmethod
    def log_activity(
        cls,
        db_session,
        action: str,
        user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> 'ActivityLog':
        """
        Helper method to log an activity.
        
        Args:
            db_session: Database session
            action: The action being logged
            user_id: ID of the user who performed the action
            entity_type: Type of entity this activity is related to
            entity_id: ID of the entity this activity is related to
            details: Additional details about the activity
            ip_address: IP address of the user
            user_agent: User agent string of the client
            
        Returns:
            The created ActivityLog instance
        """
        activity = cls(
            action=action,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db_session.add(activity)
        db_session.commit()
        
        return activity
