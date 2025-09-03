"""
Lead model for the Tesla CRM application.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Text, Enum, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
import json

from .base import Base
from app.schemas.lead import LeadStatus, LeadSource

class Lead(Base):
    """Lead model representing potential customers or clients."""
    __tablename__ = "leads"
    
    # Basic Information
    first_name = Column(String(100), nullable=False, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    phone = Column(String(50), index=True, nullable=True)
    company = Column(String(200), nullable=True)
    job_title = Column(String(200), nullable=True)
    
    # Lead Details
    status = Column(
        Enum(LeadStatus, values_callable=lambda x: [e.value for e in LeadStatus]),
        default=LeadStatus.NEW,
        nullable=False,
        index=True
    )
    
    source = Column(
        Enum(LeadSource, values_callable=lambda x: [e.value for e in LeadSource]),
        default=LeadSource.WEBSITE,
        nullable=False,
        index=True
    )
    
    assigned_to = Column(
        Integer,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Additional Information
    notes = Column(Text, nullable=True)
    metadata_ = Column('metadata', JSON, default=dict, nullable=False)
    
    # Relationships
    assigned_user = relationship("User", back_populates="assigned_leads", foreign_keys=[assigned_to])
    
    # Relationships
    conversations = relationship("Conversation", back_populates="lead", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        # Add composite index for common search patterns
        {'mysql_charset': 'utf8mb4', 'mysql_engine': 'InnoDB'}
    )
    
    def __repr__(self):
        return f"<Lead {self.first_name} {self.last_name} ({self.status})>"
    
    @property
    def full_name(self) -> str:
        """Return the full name of the lead."""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert lead to dictionary with proper type handling."""
        result = super().to_dict()
        
        # Convert enums to their values
        if 'status' in result:
            result['status'] = self.status.value if self.status else None
        if 'source' in result:
            result['source'] = self.source.value if self.source else None
            
        # Handle metadata
        if 'metadata_' in result:
            result['metadata'] = result.pop('metadata_')
            
        return result
