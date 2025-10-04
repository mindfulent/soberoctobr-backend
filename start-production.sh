#!/bin/bash
# Production startup script for DigitalOcean App Platform

echo "Starting Sober October Backend in production mode..."

# Print environment info for debugging
echo "PORT: ${PORT}"
echo "DATABASE_URL is set: $(if [ -n "$DATABASE_URL" ]; then echo "YES"; else echo "NO"; fi)"
echo "Python version: $(python --version)"

# Run database migrations
echo "Running database migrations..."
if alembic upgrade head; then
    echo "Migrations completed successfully"
else
    echo "WARNING: Migration failed, but continuing to start the app..."
    echo "The app may not function correctly without a proper database"
fi

# Start the application
echo "Starting uvicorn server on port ${PORT:-8080}..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info

