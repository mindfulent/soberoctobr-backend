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
from app.api import auth, users, challenges, habits, entries, habit_templates, admin

# Optional Sentry integration
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking and performance monitoring
# Only in production or if explicitly enabled
is_production = settings.ENVIRONMENT == "production"

if SENTRY_AVAILABLE and settings.SENTRY_DSN and (is_production or settings.SENTRY_ENABLED):
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,

        # Performance Monitoring
        integrations=[
            FastApiIntegration(),
            StarletteIntegration(),
        ],

        # Performance monitoring - sample 100% in production initially
        traces_sample_rate=1.0 if is_production else 0.0,

        # Don't send events in development unless explicitly enabled
        before_send=lambda event, hint: event if (is_production or settings.SENTRY_ENABLED) else None,
    )

    logger.info("✓ Sentry initialized for error tracking")
elif not SENTRY_AVAILABLE:
    logger.info("Sentry SDK not installed (optional dependency)")
else:
    logger.info("Sentry disabled (no DSN or not enabled)")


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
# Configure to use field aliases (camelCase) in JSON responses
app = FastAPI(
    title="Sober October API",
    description="Backend API for the Sober October habit tracking application",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure default response model behavior to use aliases
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

# Override default response class to use by_alias=True
class CamelCaseJSONResponse(JSONResponse):
    """JSON response that uses camelCase field names (aliases)."""
    def render(self, content) -> bytes:
        return super().render(
            jsonable_encoder(content, by_alias=True)
        )

app.router.default_response_class = CamelCaseJSONResponse

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add HTTP logging middleware for debugging integration issues
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class HTTPLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.
    Helps debug frontend-backend integration issues.
    """
    async def dispatch(self, request: Request, call_next):
        # Skip logging for health check endpoints (too noisy)
        if request.url.path in ["/health", "/ping"]:
            return await call_next(request)

        # Log request
        start_time = time.time()
        request_id = str(time.time())  # Simple request ID

        logger.info(f"→ [{request_id}] {request.method} {request.url.path}")
        if request.query_params:
            logger.info(f"  Query: {dict(request.query_params)}")

        # Call the endpoint
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"✗ [{request_id}] Exception: {str(e)}")
            raise

        # Log response
        duration = time.time() - start_time
        duration_ms = int(duration * 1000)

        if response.status_code < 400:
            logger.info(f"← [{request_id}] {response.status_code} ({duration_ms}ms)")
        else:
            logger.warning(f"← [{request_id}] {response.status_code} ({duration_ms}ms)")

        return response

# Add the logging middleware
if settings.DEBUG:
    logger.info("Debug mode enabled - adding HTTP logging middleware")
    app.add_middleware(HTTPLoggingMiddleware)


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
app.include_router(habit_templates.router, prefix="/api/v1", tags=["habit-templates"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

