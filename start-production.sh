#!/bin/bash
# Production startup script for DigitalOcean App Platform

set -e

echo "Starting Sober October Backend in production mode..."

# Run database migrations
echo "Running database migrations..."
alembic upgrade head || echo "Warning: Migration failed or no migrations to run"

# Start the application
echo "Starting uvicorn server on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}

