@echo off
REM DiveTrader Development Startup Script for Windows
REM This script starts both the backend and frontend development servers

echo 🏊‍♂️ Starting DiveTrader Development Environment...

REM Check if we're in the right directory
if not exist "CLAUDE.md" (
    echo ❌ Error: Please run this script from the diveTrader root directory
    pause
    exit /b 1
)

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules" (
    echo 📦 Installing frontend dependencies...
    cd frontend
    npm install
    cd ..
)

echo.
echo 🚀 Starting Backend API Server...
cd backend

REM Activate virtual environment and start backend in new window
if exist "venv\Scripts\activate.bat" (
    start "DiveTrader Backend" cmd /c "venv\Scripts\activate.bat && python main.py"
) else (
    start "DiveTrader Backend" cmd /c "python main.py"
)

cd ..

REM Wait for backend to start
timeout /t 3 /nobreak > nul

echo 🚀 Starting Frontend Development Server...
cd frontend

REM Start frontend in new window
start "DiveTrader Frontend" cmd /c "npm run dev"

cd ..

echo.
echo ✅ DiveTrader is starting in separate windows!
echo.
echo 📊 Frontend Dashboard: http://localhost:5173
echo 🔧 Backend API: http://localhost:8000
echo 📋 API Docs: http://localhost:8000/docs
echo.
echo Check the opened command windows for logs
echo Close the command windows to stop the servers
echo.
pause