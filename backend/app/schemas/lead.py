"""
Lead-related Pydantic schemas for the Tesla CRM application.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, validator
from .base import BaseSchema

class LeadStatus(str, Enum):
    """Possible statuses for a lead."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    CANCELLED = "cancelled"

class LeadSource(str, Enum):
    """Possible sources for a lead."""
    WEBSITE = "website"
    SOCIAL_MEDIA = "social_media"
    REFERRAL = "referral"
    EMAIL = "email"
    PHONE = "phone"
    CHAT = "chat"
    OTHER = "other"

class LeadBase(BaseModel):
    """Base schema for lead with common fields."""
    first_name: str = Field(..., description="First name of the lead")
    last_name: str = Field(..., description="Last name of the lead")
    email: Optional[EmailStr] = Field(None, description="Email address of the lead")
    phone: Optional[str] = Field(None, description="Phone number of the lead")
    company: Optional[str] = Field(None, description="Company name")
    job_title: Optional[str] = Field(None, description="Job title")
    status: LeadStatus = Field(LeadStatus.NEW, description="Current status of the lead")
    source: LeadSource = Field(LeadSource.WEBSITE, description="Source of the lead")
    assigned_to: Optional[int] = Field(None, description="ID of the user this lead is assigned to")
    notes: Optional[str] = Field(None, description="Additional notes about the lead")
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata for the lead"
    )

    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v is None:
            return v
        # Simple validation - can be enhanced with a proper phone number library
        v = ''.join(filter(str.isdigit, v))
        if len(v) < 10:
            raise ValueError("Phone number must be at least 10 digits")
        return v

class LeadCreate(LeadBase):
    """Schema for creating a new lead."""
    pass

class LeadUpdate(BaseModel):
    """Schema for updating an existing lead."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    status: Optional[LeadStatus] = None
    source: Optional[LeadSource] = None
    assigned_to: Optional[int] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class Lead(LeadBase, BaseSchema):
    """Complete lead schema with all fields."""
    class Config:
        orm_mode = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class LeadListResponse(BaseModel):
    """Response schema for listing leads with pagination."""
    items: List[Lead] = []
    total: int = 0
    page: int = 1
    size: int = 10
    pages: int = 1
