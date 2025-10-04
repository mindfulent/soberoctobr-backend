#!/bin/bash
# Start script for Sober October Backend

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if port 8000 is in use and kill the process
PORT=8000
PID=$(lsof -ti:$PORT)

if [ ! -z "$PID" ]; then
    echo -e "${YELLOW}⚠${NC}  Port $PORT is already in use by process $PID"
    echo "   Shutting down existing server..."
    kill -9 $PID 2>/dev/null
    sleep 1
    echo -e "${GREEN}✓${NC}  Existing server stopped"
    echo ""
fi

# Activate virtual environment
source venv/bin/activate

# Start the FastAPI server
echo "🚀 Starting Sober October Backend..."
echo "📍 API will be available at: http://localhost:8000"
echo "📚 API docs will be available at: http://localhost:8000/docs"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

