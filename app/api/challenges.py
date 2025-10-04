"""Challenge management API routes."""

import uuid
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.challenge import Challenge, ChallengeStatus
from app.schemas.challenge import ChallengeCreate, ChallengeResponse, ChallengeUpdate

router = APIRouter()


@router.get("", response_model=List[ChallengeResponse])
async def get_challenges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all challenges for the current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[ChallengeResponse]: List of user's challenges
    """
    challenges = db.query(Challenge).filter(
        Challenge.user_id == current_user.id
    ).order_by(Challenge.created_at.desc()).all()
    return challenges


@router.post("", response_model=ChallengeResponse, status_code=status.HTTP_201_CREATED)
async def create_challenge(
    challenge_data: ChallengeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new 30-day challenge.

    Args:
        challenge_data: Challenge creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChallengeResponse: Created challenge
    """
    # Calculate end date (30 days from start)
    end_date = challenge_data.start_date + timedelta(days=30)

    challenge = Challenge(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        start_date=challenge_data.start_date,
        end_date=end_date,
        status=ChallengeStatus.ACTIVE
    )

    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


@router.get("/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge(
    challenge_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific challenge by ID.

    Args:
        challenge_id: Challenge ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChallengeResponse: Challenge details

    Raises:
        HTTPException: If challenge not found or not owned by user
    """
    challenge = db.query(Challenge).filter(
        Challenge.id == challenge_id,
        Challenge.user_id == current_user.id
    ).first()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )

    return challenge


@router.put("/{challenge_id}", response_model=ChallengeResponse)
async def update_challenge(
    challenge_id: str,
    challenge_update: ChallengeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a challenge's status.

    Args:
        challenge_id: Challenge ID
        challenge_update: Challenge update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChallengeResponse: Updated challenge

    Raises:
        HTTPException: If challenge not found or not owned by user
    """
    challenge = db.query(Challenge).filter(
        Challenge.id == challenge_id,
        Challenge.user_id == current_user.id
    ).first()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )

    if challenge_update.status:
        challenge.status = ChallengeStatus(challenge_update.status)

    db.commit()
    db.refresh(challenge)
    return challenge


@router.delete("/{challenge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_challenge(
    challenge_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a challenge.

    Args:
        challenge_id: Challenge ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If challenge not found or not owned by user
    """
    challenge = db.query(Challenge).filter(
        Challenge.id == challenge_id,
        Challenge.user_id == current_user.id
    ).first()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )

    db.delete(challenge)
    db.commit()
