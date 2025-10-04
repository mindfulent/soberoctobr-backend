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
        default=30,
        description="Token expiration time in minutes"
    )
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
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
