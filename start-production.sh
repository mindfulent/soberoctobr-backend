#!/bin/bash
# Production startup script for DigitalOcean App Platform

set -e  # Exit on error

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
echo ""

# Verify required environment variables
echo "Verifying required environment variables..."
MISSING_VARS=0

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL is not set"
    MISSING_VARS=1
fi

if [ -z "$SECRET_KEY" ]; then
    echo "ERROR: SECRET_KEY is not set"
    MISSING_VARS=1
fi

if [ $MISSING_VARS -eq 1 ]; then
    echo "ERROR: Missing required environment variables. Cannot start."
    exit 1
fi

echo "All required environment variables are set."
echo ""

# Test database connection
echo "Testing database connection..."
python -c "
from app.config import settings
from sqlalchemy import create_engine, text
import sys

try:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✓ Database connection successful')
except Exception as e:
    print(f'✗ Database connection failed: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "ERROR: Cannot connect to database. Exiting."
    exit 1
fi
echo ""

# Run database migrations
echo "Running database migrations..."
if alembic upgrade head; then
    echo "✓ Migrations completed successfully"
else
    echo "✗ ERROR: Migration failed"
    echo "Cannot start application without successful migration"
    exit 1
fi
echo ""

# Start the application
echo "========================================="
echo "Starting uvicorn server"
echo "  Host: 0.0.0.0"
echo "  Port: ${PORT:-8080}"
echo "========================================="
echo ""

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8080} \
    --log-level info \
    --access-log \
    --no-use-colors
