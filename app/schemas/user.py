"""User Pydantic schemas."""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from app.schemas.base import base_response_config


class UserBase(BaseModel):
    """Base user schema with common attributes."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    google_id: str
    picture: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: str
    picture: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = base_response_config
