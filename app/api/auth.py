"""Authentication API routes."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token, get_current_user
from app.core.oauth import exchange_code_for_token, get_google_user_info
from app.models.user import User
from app.schemas.auth import Token, GoogleAuthRequest
from app.schemas.user import UserResponse

router = APIRouter()


@router.post("/google", response_model=Token)
async def google_auth(
    auth_request: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user with Google OAuth and return JWT token.

    Args:
        auth_request: Google OAuth authorization code and redirect URI
        db: Database session

    Returns:
        Token: JWT access token

    Raises:
        HTTPException: If authentication fails
    """
    # Exchange authorization code for access token
    token_data = await exchange_code_for_token(
        auth_request.code,
        auth_request.redirect_uri
    )

    # Get user info from Google
    user_info = await get_google_user_info(token_data["access_token"])

    # Check if user exists
    user = db.query(User).filter(User.google_id == user_info["id"]).first()

    if not user:
        # Create new user
        user = User(
            id=str(uuid.uuid4()),
            email=user_info["email"],
            name=user_info["name"],
            picture=user_info.get("picture"),
            google_id=user_info["id"]
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create JWT token
    access_token = create_access_token(data={"sub": user.id})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user from JWT token

    Returns:
        UserResponse: Current user information
    """
    return current_user


@router.post("/logout")
async def logout():
    """
    Logout endpoint (client-side token removal).

    Returns:
        dict: Success message

    Note:
        With JWT tokens, actual logout is handled client-side by removing the token.
        This endpoint exists for consistency and future server-side token blacklisting.
    """
    return {"message": "Successfully logged out"}
