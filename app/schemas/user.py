"""User Pydantic schemas."""

from pydantic import BaseModel, EmailStr, Field, computed_field
from datetime import datetime
from typing import Optional
from app.schemas.base import base_response_config
from app.core.security import is_admin


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

    @computed_field
    @property
    def is_admin(self) -> bool:
        """Check if user is an admin based on email."""
        return is_admin(self.email)

    model_config = base_response_config
