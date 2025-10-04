"""Habit management API routes."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.challenge import Challenge
from app.models.habit import Habit
from app.schemas.habit import HabitCreate, HabitResponse, HabitUpdate, HabitBulkCreate

router = APIRouter()


@router.get("/challenges/{challenge_id}/habits", response_model=List[HabitResponse])
async def get_challenge_habits(
    challenge_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all habits for a specific challenge.

    Args:
        challenge_id: Challenge ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[HabitResponse]: List of habits in the challenge

    Raises:
        HTTPException: If challenge not found or not owned by user
    """
    # Verify challenge ownership
    challenge = db.query(Challenge).filter(
        Challenge.id == challenge_id,
        Challenge.user_id == current_user.id
    ).first()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )

    habits = db.query(Habit).filter(
        Habit.challenge_id == challenge_id
    ).order_by(Habit.order).all()

    return habits


@router.post("/challenges/{challenge_id}/habits", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
async def create_habit(
    challenge_id: str,
    habit_data: HabitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new habit within a challenge.

    Args:
        challenge_id: Challenge ID
        habit_data: Habit creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        HabitResponse: Created habit

    Raises:
        HTTPException: If challenge not found or habit limit exceeded
    """
    # Verify challenge ownership
    challenge = db.query(Challenge).filter(
        Challenge.id == challenge_id,
        Challenge.user_id == current_user.id
    ).first()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )

    # Check habit count limit (max 10)
    habit_count = db.query(Habit).filter(
        Habit.challenge_id == challenge_id,
        Habit.is_active == True
    ).count()

    if habit_count >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum of 10 habits per challenge"
        )

    habit = Habit(
        id=str(uuid.uuid4()),
        challenge_id=challenge_id,
        name=habit_data.name,
        type=habit_data.type,
        target_count=habit_data.target_count,
        preferred_time=habit_data.preferred_time,
        order=habit_data.order or habit_count,
        template_id=habit_data.template_id
    )

    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit


@router.get("/habits/{habit_id}", response_model=HabitResponse)
async def get_habit(
    habit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific habit by ID.

    Args:
        habit_id: Habit ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        HabitResponse: Habit details

    Raises:
        HTTPException: If habit not found or not owned by user
    """
    habit = db.query(Habit).join(Challenge).filter(
        Habit.id == habit_id,
        Challenge.user_id == current_user.id
    ).first()

    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found"
        )

    return habit


@router.put("/habits/{habit_id}", response_model=HabitResponse)
async def update_habit(
    habit_id: str,
    habit_update: HabitUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a habit.

    Args:
        habit_id: Habit ID
        habit_update: Habit update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        HabitResponse: Updated habit

    Raises:
        HTTPException: If habit not found or not owned by user
    """
    habit = db.query(Habit).join(Challenge).filter(
        Habit.id == habit_id,
        Challenge.user_id == current_user.id
    ).first()

    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found"
        )

    # Update fields if provided
    if habit_update.name is not None:
        habit.name = habit_update.name
    if habit_update.type is not None:
        habit.type = habit_update.type
    if habit_update.target_count is not None:
        habit.target_count = habit_update.target_count
    if habit_update.preferred_time is not None:
        habit.preferred_time = habit_update.preferred_time
    if habit_update.order is not None:
        habit.order = habit_update.order
    if habit_update.is_active is not None:
        habit.is_active = habit_update.is_active

    db.commit()
    db.refresh(habit)
    return habit


@router.delete("/habits/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_habit(
    habit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a habit (or archive it by setting is_active=False).

    Args:
        habit_id: Habit ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If habit not found or not owned by user
    """
    habit = db.query(Habit).join(Challenge).filter(
        Habit.id == habit_id,
        Challenge.user_id == current_user.id
    ).first()

    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found"
        )

    # Archive instead of delete to preserve historical data
    habit.is_active = False
    db.commit()


@router.post("/challenges/{challenge_id}/habits/bulk", response_model=List[HabitResponse], status_code=status.HTTP_201_CREATED)
async def create_habits_bulk(
    challenge_id: str,
    bulk_data: HabitBulkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create multiple habits at once within a challenge (for onboarding).

    Args:
        challenge_id: Challenge ID
        bulk_data: Bulk habit creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[HabitResponse]: List of created habits

    Raises:
        HTTPException: If challenge not found, habit limit exceeded, or validation fails
    """
    # Verify challenge ownership
    challenge = db.query(Challenge).filter(
        Challenge.id == challenge_id,
        Challenge.user_id == current_user.id
    ).first()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )

    # Check current habit count
    current_habit_count = db.query(Habit).filter(
        Habit.challenge_id == challenge_id,
        Habit.is_active == True
    ).count()

    # Check if bulk creation would exceed limit
    total_habits = current_habit_count + len(bulk_data.habits)
    if total_habits > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum of 10 habits per challenge. Current: {current_habit_count}, Attempting to add: {len(bulk_data.habits)}"
        )

    # Create all habits
    created_habits = []
    for idx, habit_data in enumerate(bulk_data.habits):
        habit = Habit(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            name=habit_data.name,
            type=habit_data.type,
            target_count=habit_data.target_count,
            preferred_time=habit_data.preferred_time,
            order=habit_data.order if habit_data.order is not None else (current_habit_count + idx),
            template_id=habit_data.template_id
        )
        db.add(habit)
        created_habits.append(habit)

    # Commit all at once
    db.commit()
    
    # Refresh all to get database-generated fields
    for habit in created_habits:
        db.refresh(habit)

    return created_habits
