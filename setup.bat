@echo off
REM LLM Deploy - Quick Start Script for Windows
REM This script sets up and runs both backend and frontend

echo.
echo ========================================
echo  LLM Deploy - Full Stack Setup
echo ========================================
echo.

REM Check if backend venv exists
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate venv and install dependencies
echo.
echo Installing backend dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt > nul 2>&1

REM Check if frontend node_modules exists
cd frontend
if not exist "node_modules" (
    echo.
    echo Installing frontend dependencies...
    call npm install > nul 2>&1
)
cd ..

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo To start the application:
echo.
echo Terminal 1 (Backend):
echo   venv\Scripts\activate
echo   python -m app.main
echo.
echo Terminal 2 (Frontend):
echo   cd frontend
echo   npm run dev
echo.
echo Frontend: http://localhost:5173
echo Backend API: http://localhost:8000
echo Swagger UI: http://localhost:8000/docs
echo.

pause
