#!/bin/bash
# Production startup script for DigitalOcean App Platform

echo "========================================="
echo "Starting Sober October Backend"
echo "========================================="

# Print environment info for debugging
echo "Environment Information:"
echo "  PORT: ${PORT:-8080}"
echo "  ENVIRONMENT: ${ENVIRONMENT:-not set}"
echo "  DATABASE_URL: $(if [ -n "$DATABASE_URL" ]; then echo "SET (${#DATABASE_URL} chars)"; else echo "NOT SET"; fi)"
echo "  FRONTEND_URL: ${FRONTEND_URL:-not set}"
echo "  CORS_ORIGINS: ${CORS_ORIGINS:-not set}"
echo "  Python version: $(python --version)"
echo "  Working directory: $(pwd)"
echo "  Python packages:"
python -c "import fastapi, uvicorn, sqlalchemy, alembic; print(f'    fastapi={fastapi.__version__}, uvicorn={uvicorn.__version__}, sqlalchemy={sqlalchemy.__version__}')" || echo "    Error checking versions"
echo ""

# Verify critical environment variables
echo "Verifying environment variables..."
if [ -z "$DATABASE_URL" ]; then
    echo "WARNING: DATABASE_URL is not set - using default"
fi
if [ -z "$SECRET_KEY" ]; then
    echo "WARNING: SECRET_KEY is not set - using default (NOT SECURE)"
fi
echo ""

# Test Python imports
echo "Testing Python imports..."
python -c "
import sys
try:
    from app.main import app
    print('✓ Successfully imported FastAPI app')
except Exception as e:
    print(f'✗ Failed to import app: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" || {
    echo "FATAL: Cannot import application. Check for syntax errors or missing dependencies."
    exit 1
}
echo ""

# Test database connection (non-blocking)
echo "Testing database connection..."
python -c "
from app.config import settings
from sqlalchemy import create_engine, text
import sys

try:
    print(f'  Attempting connection to: {settings.DATABASE_URL[:50]}...')
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args={'connect_timeout': 5})
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('  ✓ Database connection successful')
except Exception as e:
    print(f'  ✗ Database connection failed: {e}')
    print('  WARNING: App will start but database operations will fail')
" || echo "  Database test failed but continuing..."
echo ""

# Run database migrations (with timeout and better error handling)
echo "Running database migrations..."
if timeout 45 alembic upgrade head 2>&1 | tee /tmp/migration.log; then
    echo "✓ Migrations completed successfully"
else
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        echo "⚠ WARNING: Migration timed out after 45 seconds"
    else
        echo "⚠ WARNING: Migration failed with exit code $EXIT_CODE"
    fi
    echo "App will start anyway - check logs for database issues"
    # Print last few lines of migration log if available
    if [ -f /tmp/migration.log ]; then
        echo "Last migration output:"
        tail -n 10 /tmp/migration.log
    fi
fi
echo ""

# Start the application
echo "========================================="
echo "Starting uvicorn server"
echo "  Host: 0.0.0.0"
echo "  Port: ${PORT:-8080}"
echo "  Log Level: info"
echo "========================================="
echo ""

# Use exec to replace the shell process with uvicorn
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8080} \
    --log-level info \
    --timeout-keep-alive 30 \
    --access-log
