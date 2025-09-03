"""
Base Pydantic schemas for the Tesla CRM application.
"""
from datetime import datetime
from typing import Optional, Generic, TypeVar, Any
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

# Generic type for pagination responses
DataT = TypeVar('DataT')

class BaseResponse(GenericModel, Generic[DataT]):
    """Base response model with success flag and optional message."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[DataT] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        orm_mode = True
        arbitrary_types_allowed = True

class BaseSchema(BaseModel):
    """Base schema with common fields."""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
