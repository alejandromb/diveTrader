#!/bin/bash

echo "🛑 Stopping all DiveTrader processes..."

# Kill all related processes
pkill -f "python.*main.py"
pkill -f "uvicorn"
pkill -f "fastapi"
pkill -f "npm run dev"
pkill -f "vite"
pkill -f "node.*vite"

# Kill processes using our ports
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

echo "⏳ Waiting for processes to stop..."
sleep 3

echo "🧹 Cleaning up..."
cd "$(dirname "$0")"

# Clean frontend build cache
cd frontend
rm -rf dist/ node_modules/.vite/ 2>/dev/null || true
cd ..

# Clean Python cache
find backend -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find backend -name "*.pyc" -delete 2>/dev/null || true

echo "🚀 Starting fresh DiveTrader environment..."

# Start backend
cd backend
echo "🐍 Starting SQLModel Backend API Server..."
python3 main_sqlmodel.py > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Backend failed to start. Check backend.log"
    tail -10 backend.log
    exit 1
fi

cd ../frontend
echo "⚛️ Starting Frontend Development Server..."
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

cd ..

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
echo "🛑 To stop: ./stop.sh"
echo ""

# Save PIDs for stopping later
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

echo "🎉 Ready to use! Check http://localhost:5173"