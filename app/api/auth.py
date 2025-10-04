"""Authentication API routes."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token, get_current_user
from app.core.oauth import exchange_code_for_token, get_google_user_info
from app.models.user import User
from app.schemas.auth import Token, GoogleAuthRequest
from app.schemas.user import UserResponse
from app.config import settings

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


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str = "",
    db: Session = Depends(get_db)
):
    """
    Google OAuth callback endpoint.
    
    This endpoint is called by Google after user authorizes the app.
    It exchanges the authorization code for an access token, gets user info,
    creates/updates the user, generates a JWT, and redirects to frontend with token.
    
    Args:
        code: Authorization code from Google OAuth
        state: State parameter containing the frontend URL (optional)
        db: Database session
        
    Returns:
        RedirectResponse: Redirects to frontend with JWT token in query params
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # The redirect_uri must match what was sent to Google OAuth
        # This is the backend callback URL (where we are now)
        # Use configured redirect URI or construct from API base URL
        redirect_uri = f"{settings.API_BASE_URL}/api/auth/google/callback"
        
        # Exchange authorization code for access token
        token_data = await exchange_code_for_token(code, redirect_uri)
        
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
        
        # Use state parameter as frontend URL if provided, otherwise use configured FRONTEND_URL
        frontend_url = state if state else settings.FRONTEND_URL
        
        # Validate that frontend_url is a localhost URL for security
        if not (frontend_url.startswith("http://localhost:") or 
                frontend_url.startswith("https://localhost:") or
                frontend_url == settings.FRONTEND_URL):
            frontend_url = settings.FRONTEND_URL
        
        # Redirect to frontend with token
        # Frontend will extract token from URL and store it
        frontend_callback_url = f"{frontend_url}/auth/callback?token={access_token}"
        return RedirectResponse(url=frontend_callback_url)
        
    except HTTPException as e:
        # Log the error and redirect to frontend with error
        print(f"HTTPException during Google OAuth callback: {str(e)}")
        frontend_url = state if state and state.startswith("http://localhost:") else settings.FRONTEND_URL
        error_url = f"{frontend_url}/?error=auth_failed&detail=http_exception"
        return RedirectResponse(url=error_url)
    except Exception as e:
        # Log the error and redirect with error message
        print(f"Error during Google OAuth callback: {str(e)}")
        import traceback
        traceback.print_exc()
        frontend_url = state if state and state.startswith("http://localhost:") else settings.FRONTEND_URL
        error_url = f"{frontend_url}/?error=auth_failed&detail=exception"
        return RedirectResponse(url=error_url)
