"""
Habit Template Schemas
Pydantic models for habit template API responses
"""

from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.base import base_response_config


class HabitTemplateResponse(BaseModel):
    """Schema for habit template response."""
    
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    type: str = Field(..., description="Habit type (binary or counted)")
    preferred_time: str = Field(..., description="Preferred time of day")
    target_count: Optional[int] = Field(None, description="Target count for counted habits")
    icon: str = Field(..., description="Icon/emoji for the template")
    category: str = Field(..., description="Template category")
    
    model_config = base_response_config

