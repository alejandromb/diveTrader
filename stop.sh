#!/bin/bash

echo "🛑 Stopping DiveTrader..."

cd "$(dirname "$0")"

# Kill PIDs if they exist
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    kill $BACKEND_PID 2>/dev/null || true
    rm .backend.pid
    echo "Stopped backend (PID: $BACKEND_PID)"
fi

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    kill $FRONTEND_PID 2>/dev/null || true
    rm .frontend.pid
    echo "Stopped frontend (PID: $FRONTEND_PID)"
fi

# Kill all related processes
pkill -f "python.*main.py"
pkill -f "uvicorn"
pkill -f "npm run dev"
pkill -f "vite"
pkill -f "node.*vite"

# Kill processes using our ports
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

echo "✅ DiveTrader stopped"