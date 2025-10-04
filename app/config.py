"""
Application configuration settings.

This module handles environment variable loading and application
configuration using Pydantic settings.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        DATABASE_URL: PostgreSQL database connection string
        SECRET_KEY: Secret key for JWT token signing
        ALGORITHM: Algorithm for JWT token signing
        ACCESS_TOKEN_EXPIRE_MINUTES: Token expiration time in minutes
        CORS_ORIGINS: List of allowed CORS origins
        GOOGLE_CLIENT_ID: Google OAuth client ID
        GOOGLE_CLIENT_SECRET: Google OAuth client secret
        GOOGLE_REDIRECT_URI: OAuth redirect URI
        FRONTEND_URL: Frontend application URL
        ENVIRONMENT: Application environment (development, production)
        DEBUG: Debug mode flag
        LOG_LEVEL: Logging level
    """

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://username:password@localhost:5432/soberoctobr_db",
        description="PostgreSQL database connection string"
    )

    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-here-change-in-production",
        description="Secret key for JWT token signing"
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="Algorithm for JWT token signing"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=1440,  # 24 hours
        description="Token expiration time in minutes"
    )

    # Google OAuth
    GOOGLE_CLIENT_ID: str = Field(
        default="",
        description="Google OAuth client ID"
    )
    GOOGLE_CLIENT_SECRET: str = Field(
        default="",
        description="Google OAuth client secret"
    )
    GOOGLE_REDIRECT_URI: str = Field(
        default="http://localhost:5173/auth/callback",
        description="OAuth redirect URI"
    )

    # API
    API_BASE_URL: str = Field(
        default="http://localhost:8000",
        description="Backend API base URL"
    )

    # Frontend
    FRONTEND_URL: str = Field(
        default="http://localhost:5173",
        description="Frontend application URL"
    )

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
            "http://localhost:8082",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:8082"
        ],
        description="List of allowed CORS origins"
    )

    # Environment
    ENVIRONMENT: str = Field(
        default="development",
        description="Application environment"
    )
    DEBUG: bool = Field(
        default=True,
        description="Debug mode flag"
    )

    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()

