"""Habit Pydantic schemas."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class HabitType(str, Enum):
    """Habit type enumeration."""
    BINARY = "binary"
    COUNTED = "counted"


class HabitBase(BaseModel):
    """Base habit schema."""
    name: str = Field(..., min_length=1, max_length=200)
    type: HabitType
    target_count: Optional[int] = Field(None, ge=1)
    preferred_time: Optional[str] = Field(None, max_length=50)


class HabitCreate(HabitBase):
    """Schema for creating a new habit."""
    order: Optional[int] = Field(0, ge=0)
    template_id: Optional[str] = Field(None, max_length=100)


class HabitUpdate(BaseModel):
    """Schema for updating a habit."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[HabitType] = None
    target_count: Optional[int] = Field(None, ge=1)
    preferred_time: Optional[str] = Field(None, max_length=50)
    order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class HabitResponse(HabitBase):
    """Schema for habit response."""
    id: str
    challenge_id: str
    order: int
    is_active: bool
    template_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HabitBulkCreate(BaseModel):
    """Schema for bulk habit creation."""
    habits: List[HabitCreate] = Field(..., min_length=1, max_length=10)
