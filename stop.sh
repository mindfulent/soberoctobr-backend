#!/bin/bash
# Stop script for Sober October Backend

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PORT=8000
PID=$(lsof -ti:$PORT)

if [ ! -z "$PID" ]; then
    echo "🛑 Stopping Sober October Backend (PID: $PID)..."
    kill -9 $PID 2>/dev/null
    sleep 1
    echo -e "${GREEN}✓${NC} Backend server stopped"
else
    echo -e "${RED}✗${NC} No backend server running on port $PORT"
fi

