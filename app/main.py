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
    
    Note: This should complete quickly to allow the app to start serving
    health check requests. Heavy operations should be deferred or async.
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
    
    # Don't test database during startup - it can slow down the health checks
    # The database connection will be tested on first use
    logger.info("✓ Application startup complete - ready to serve requests")
    
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
    Health check endpoint - lightweight version for readiness probe.
    
    This endpoint is called frequently by DigitalOcean's health checks.
    It should respond quickly without heavy operations like database queries.

    Returns:
        dict: Application health status
    """
    import os
    
    # Return immediately with basic health status
    # Do NOT check database here - it's too slow for health checks
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "port": os.getenv("PORT", "8080")
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check endpoint with database connectivity test.
    
    This endpoint is more comprehensive but slower. Use /health for
    quick readiness probes and this endpoint for detailed diagnostics.

    Returns:
        dict: Detailed application health status including database
    """
    import os
    
    # Basic health status
    health_status = {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "port": os.getenv("PORT", "8080")
    }
    
    # Try to check database connection (non-blocking)
    try:
        from app.core.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        logger.warning(f"Database check failed in health endpoint: {e}")
        health_status["database"] = "disconnected"
        health_status["database_error"] = str(e)[:100]  # Limit error message length
    
    return health_status


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

