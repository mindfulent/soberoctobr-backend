#!/bin/bash
# Production startup script for DigitalOcean App Platform
# Optimized to start the app quickly and handle migrations in background

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

# Quick validation of Python installation
echo "Validating Python environment..."
python -c "import fastapi, uvicorn; print(f'✓ Core packages available: FastAPI={fastapi.__version__}, uvicorn={uvicorn.__version__}')" || {
    echo "FATAL: Core Python packages not available"
    exit 1
}

# Quick import test (should be fast)
echo "Validating app imports..."
python -c "from app.main import app; print('✓ App imports successfully')" || {
    echo "FATAL: Cannot import application"
    exit 1
}
echo ""

# Run migrations in background - don't block app startup
# This allows health checks to pass while migrations run
echo "Starting database migrations in background..."
(
    sleep 5  # Give the app a few seconds to start serving health checks
    echo "Running alembic migrations..."
    if timeout 60 alembic upgrade head 2>&1 | tee /tmp/migration.log; then
        echo "✓ Migrations completed successfully"
    else
        EXIT_CODE=$?
        echo "⚠ WARNING: Migration failed with exit code $EXIT_CODE"
        if [ -f /tmp/migration.log ]; then
            echo "Migration output:"
            tail -n 20 /tmp/migration.log
        fi
    fi
) &

# Save the background process ID
MIGRATION_PID=$!
echo "Migration running in background (PID: $MIGRATION_PID)"
echo ""

# Start the application immediately
echo "========================================="
echo "Starting uvicorn server NOW"
echo "  Host: 0.0.0.0"
echo "  Port: ${PORT:-8080}"
echo "  Workers: 1"
echo "  Timeout: 120s"
echo "========================================="
echo ""

# Use exec to replace the shell process with uvicorn
# This ensures signals are properly handled
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8080} \
    --log-level info \
    --timeout-keep-alive 30 \
    --timeout-graceful-shutdown 10 \
    --access-log
