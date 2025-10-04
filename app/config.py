"""
Application configuration settings.

This module handles environment variable loading and application
configuration using Pydantic settings.
"""

from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import json


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
    
    @field_validator('DATABASE_URL', mode='after')
    @classmethod
    def validate_database_url(cls, v):
        """
        Validate and potentially transform DATABASE_URL.
        DigitalOcean App Platform provides DATABASE_URL, but may need adjustments.
        """
        if not v:
            raise ValueError("DATABASE_URL must be set")
        
        # Log DATABASE URL format (without exposing credentials)
        import logging
        logger = logging.getLogger(__name__)
        
        # Handle DigitalOcean's postgres:// vs postgresql:// scheme
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://", 1)
            logger.info("Converted postgres:// to postgresql:// in DATABASE_URL")
        
        return v

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

    # CORS - can be a JSON string or comma-separated string
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
            "http://localhost:8081",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:8081"
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
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """
        Parse CORS_ORIGINS from various input formats.
        
        Handles:
        - List of strings (already parsed)
        - JSON array string: '["http://example.com", "http://example2.com"]'
        - Comma-separated string: 'http://example.com,http://example2.com'
        """
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Try to parse as JSON first
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            # Fall back to comma-separated
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()

