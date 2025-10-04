"""Daily entry Pydantic schemas."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class DailyEntryBase(BaseModel):
    """Base daily entry schema."""
    date: datetime
    completed: bool = False
    count: Optional[int] = Field(None, ge=0)


class DailyEntryCreate(BaseModel):
    """Schema for creating/updating a daily entry."""
    date: datetime
    completed: Optional[bool] = False
    count: Optional[int] = Field(None, ge=0)


class DailyEntryUpdate(BaseModel):
    """Schema for updating a daily entry."""
    completed: Optional[bool] = None
    count: Optional[int] = Field(None, ge=0)


class DailyEntryResponse(DailyEntryBase):
    """Schema for daily entry response."""
    id: str
    habit_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
