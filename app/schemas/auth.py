"""Authentication Pydantic schemas."""

from pydantic import BaseModel, Field


class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    token_type: str = "bearer"


class GoogleAuthRequest(BaseModel):
    """Google OAuth authentication request schema."""
    code: str = Field(..., description="Authorization code from Google OAuth")
    redirect_uri: str = Field(..., description="Redirect URI used in OAuth flow")
