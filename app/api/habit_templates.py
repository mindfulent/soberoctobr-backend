"""
Habit Templates API routes.

This module provides endpoints for retrieving pre-configured habit templates
that users can select during onboarding.
"""

from typing import List, Optional
from fastapi import APIRouter, Query
from app.utils.habit_templates import (
    get_all_templates,
    get_template_by_id,
    get_templates_by_category,
    HabitCategory
)

router = APIRouter()


@router.get("/habit-templates", response_model=List[dict])
async def list_habit_templates(
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Get all available habit templates.
    
    This endpoint returns pre-configured habit templates that users can select
    during onboarding to quickly set up their challenge without typing.
    
    Args:
        category: Optional category filter (jons_list, physical_health, 
                 mental_wellness, daily_routines)
    
    Returns:
        List[dict]: List of habit templates with their configuration
        
    Example Response:
        [
            {
                "id": "vitamin_d",
                "name": "Vitamin D",
                "description": "Take your daily Vitamin D supplement",
                "type": "binary",
                "preferred_time": "afternoon",
                "target_count": null,
                "category": "jons_list",
                "icon": "☀️"
            },
            ...
        ]
    """
    if category:
        try:
            cat_enum = HabitCategory(category)
            return get_templates_by_category(cat_enum)
        except ValueError:
            # If invalid category, return all templates
            return get_all_templates()
    
    return get_all_templates()


@router.get("/habit-templates/{template_id}", response_model=dict)
async def get_habit_template(template_id: str):
    """
    Get a specific habit template by ID.
    
    Args:
        template_id: Unique template identifier
        
    Returns:
        dict: Template configuration
        
    Raises:
        HTTPException: If template not found (404)
        
    Example Response:
        {
            "id": "meditate",
            "name": "Meditate",
            "description": "Practice mindfulness meditation",
            "type": "binary",
            "preferred_time": "morning",
            "target_count": null,
            "category": "mental_wellness",
            "icon": "🧘‍♀️"
        }
    """
    from fastapi import HTTPException, status
    
    template = get_template_by_id(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with id '{template_id}' not found"
        )
    
    return template

