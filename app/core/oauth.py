"""Google OAuth 2.0 authentication utilities."""

from typing import Dict, Optional
import httpx
from fastapi import HTTPException, status
from app.config import settings

# Google OAuth 2.0 endpoints
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


async def exchange_code_for_token(code: str, redirect_uri: str) -> Dict[str, str]:
    """
    Exchange Google OAuth authorization code for access token.

    Args:
        code: Authorization code from Google
        redirect_uri: Redirect URI used in OAuth flow

    Returns:
        Dict containing access_token and other token info

    Raises:
        HTTPException: If token exchange fails
    """
    import logging
    logger = logging.getLogger(__name__)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )

        if response.status_code != 200:
            # Log the actual error from Google for debugging
            error_detail = response.text
            logger.error(f"Google token exchange failed. Status: {response.status_code}, Response: {error_detail}")
            logger.error(f"Redirect URI used: {redirect_uri}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange authorization code for token: {error_detail}",
            )

        return response.json()


async def get_google_user_info(access_token: str) -> Optional[Dict[str, str]]:
    """
    Get user information from Google using access token.

    Args:
        access_token: Google OAuth access token

    Returns:
        Dict containing user info (email, name, picture, id)

    Raises:
        HTTPException: If user info request fails
    """
    import logging
    logger = logging.getLogger(__name__)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if response.status_code != 200:
            # Log the actual error from Google for debugging
            error_detail = response.text
            logger.error(f"Google user info fetch failed. Status: {response.status_code}, Response: {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get user info from Google: {error_detail}",
            )

        return response.json()
