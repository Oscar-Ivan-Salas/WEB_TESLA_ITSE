"""
Database models for the Tesla CRM application.
"""

# Import all models here to make them available when importing from app.models
from .base import Base
from .user import User, UserRole, UserStatus
from .lead import Lead
from .conversation import Conversation, Message
from .activity import ActivityLog

# Make all models available for Alembic migrations
__all__ = [
    'Base',
    'User',
    'UserRole',
    'UserStatus',
    'Lead',
    'Conversation',
    'Message',
    'ActivityLog',
]
