"""
Main FastAPI application entry point.

This module creates and configures the FastAPI application instance,
including middleware, CORS settings, and route registration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# Create FastAPI application instance
app = FastAPI(
    title="Sober October API",
    description="Backend API for the Sober October habit tracking application",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
    return {"status": "healthy", "version": "0.1.0"}


# Include API routes
# from app.api import auth, habits, users
# app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
# app.include_router(habits.router, prefix="/api/habits", tags=["habits"])
# app.include_router(users.router, prefix="/api/users", tags=["users"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
