"""Challenge Pydantic schemas."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from app.schemas.base import base_response_config
from app.schemas.habit import HabitResponse


class ChallengeBase(BaseModel):
    """Base challenge schema."""
    start_date: datetime
    end_date: datetime


class ChallengeCreate(BaseModel):
    """Schema for creating a new challenge."""
    start_date: datetime = Field(..., description="Challenge start date")


class ChallengeUpdate(BaseModel):
    """Schema for updating a challenge."""
    status: Optional[str] = Field(None, description="Challenge status")


class ChallengeResponse(ChallengeBase):
    """Schema for challenge response."""
    id: str
    user_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    habits: List["HabitResponse"] = []

    model_config = base_response_config
