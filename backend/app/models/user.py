"""
User model for authentication and authorization.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum, Enum as PyEnum
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, Text, Index
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
import bcrypt

from .base import Base

class UserRole(PyEnum):
    """User roles for authorization."""
    ADMIN = "admin"
    AGENT = "agent"
    MANAGER = "manager"
    SUPPORT = "support"

class UserStatus(str, Enum):
    """User account statuses."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    # Authentication
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # User Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    # Contact Information
    phone = Column(String(50), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    
    # Status and Roles
    role = Column(
        SQLEnum(UserRole),
        default=UserRole.AGENT,
        nullable=False,
        index=True
    )
    
    status = Column(
        SQLEnum(UserStatus),
        default=UserStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Timestamps
    last_login_at = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    
    # Relationships
    assigned_leads = relationship("Lead", back_populates="assigned_user", foreign_keys="Lead.assigned_to")
    activities = relationship("ActivityLog", back_populates="user")
    
    # Indexes
    __table_args__ = (
        # Add composite index for common search patterns
        Index('ix_users_name', 'first_name', 'last_name'),
        {'mysql_charset': 'utf8mb4', 'mysql_engine': 'InnoDB'}
    )
    
    def __init__(self, **kwargs):
        if 'password' in kwargs:
            password = kwargs.pop('password')
            self.set_password(password)
        super().__init__(**kwargs)
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
    
    @property
    def full_name(self) -> str:
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}"
    
    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        if not password:
            raise ValueError("Password cannot be empty")
        
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the stored hash."""
        if not password or not self.hashed_password:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password.encode('utf-8'))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary, excluding sensitive information."""
        result = super().to_dict()
        
        # Remove sensitive information
        result.pop('hashed_password', None)
        
        # Convert enums to their values
        if 'role' in result:
            result['role'] = self.role.value if self.role else None
        if 'status' in result:
            result['status'] = self.status.value if self.status else None
            
        # Add full name
        result['full_name'] = self.full_name
        
        return result
