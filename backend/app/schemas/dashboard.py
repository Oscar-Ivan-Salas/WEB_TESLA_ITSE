"""
Pydantic models for dashboard-related schemas.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class ActivityLogBase(BaseModel):
    """Base schema for activity log entries."""
    id: int
    action: str
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""
    total_leads: int
    new_leads: int
    active_users: int
    conversion_rate: float
    recent_activities: List[ActivityLogBase]

    class Config:
        from_attributes = True
