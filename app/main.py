"""
Main FastAPI application entry point.

This module creates and configures the FastAPI application instance,
including middleware, CORS settings, and route registration.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.api import auth, users, challenges, habits, entries

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle events for the FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 50)
    logger.info("Application Startup")
    logger.info("=" * 50)
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info(f"Database URL: {settings.DATABASE_URL[:30]}...")
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
    logger.info(f"Frontend URL: {settings.FRONTEND_URL}")
    logger.info(f"API Base URL: {settings.API_BASE_URL}")
    logger.info("=" * 50)
    
    # Test database connection (non-blocking)
    try:
        from app.core.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Database connection verified")
    except Exception as e:
        logger.warning(f"⚠ Database connection issue during startup: {e}")
        logger.warning("Application will start but database operations may fail")
    
    logger.info("✓ Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown")


# Create FastAPI application instance
app = FastAPI(
    title="Sober October API",
    description="Backend API for the Sober October habit tracking application",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    Root endpoint for health check.

    Returns:
        dict: Simple greeting message
    """
    return {"message": "Welcome to the Sober October API!"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Application health status
    """
    import os
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "port": os.getenv("PORT", "8080")
    }


@app.get("/ping")
async def ping():
    """
    Simple ping endpoint for basic connectivity testing.
    
    Returns:
        dict: Simple pong response
    """
    return {"ping": "pong"}


# Include API routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(challenges.router, prefix="/api/v1/challenges", tags=["challenges"])
app.include_router(habits.router, prefix="/api/v1", tags=["habits"])
app.include_router(entries.router, prefix="/api/v1", tags=["entries"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

