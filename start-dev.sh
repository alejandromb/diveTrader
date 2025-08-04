#!/bin/bash

# DiveTrader Development Startup Script
# This script starts both the backend and frontend development servers

echo "🏊‍♂️ Starting DiveTrader Development Environment..."

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down DiveTrader..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up trap for cleanup on script exit
trap cleanup INT TERM EXIT

# Check if we're in the right directory
if [ ! -f "CLAUDE.md" ]; then
    echo "❌ Error: Please run this script from the diveTrader root directory"
    exit 1
fi

# Check if backend dependencies are installed
if [ ! -d "backend/venv" ] && [ ! -f "backend/.env" ]; then
    echo "⚠️  Backend not fully set up. Please ensure:"
    echo "   1. Virtual environment is created: cd backend && python -m venv venv"
    echo "   2. Dependencies installed: source venv/bin/activate && pip install -r requirements.txt"
    echo "   3. .env file exists with Alpaca API keys"
    exit 1
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install
    cd ..
fi

echo ""
echo "🚀 Starting Backend API Server..."
cd backend

# Activate virtual environment and start backend
source venv/bin/activate 2>/dev/null || {
    echo "⚠️  Virtual environment not found, trying without activation..."
}

# Try python3 first, then python
if command -v python3 &> /dev/null; then
    python3 main.py > ../backend.log 2>&1 &
elif command -v python &> /dev/null; then
    python main.py > ../backend.log 2>&1 &
else
    echo "❌ Error: Neither python3 nor python command found"
    exit 1
fi
BACKEND_PID=$!

cd ..

# Wait a moment for backend to start
sleep 3

echo "🚀 Starting Frontend Development Server..."
cd frontend

# Start frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!

cd ..

# Wait for servers to initialize
sleep 5

echo ""
echo "✅ DiveTrader is running!"
echo ""
echo "📊 Frontend Dashboard: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📋 API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   Backend: tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "Press Ctrl+C to stop all servers"

# Keep script running and show logs
tail -f backend.log frontend.log 2>/dev/null