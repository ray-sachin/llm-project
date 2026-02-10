#!/usr/bin/env pwsh

# LLM Deploy - Quick Start Script for PowerShell
# This script sets up and runs both backend and frontend

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  LLM Deploy - Full Stack Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if backend venv exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate venv and install dependencies
Write-Host "`nInstalling backend dependencies..." -ForegroundColor Yellow
& ./venv/Scripts/Activate.ps1
pip install -q -r requirements.txt 2>$null

# Check if frontend node_modules exists
Push-Location frontend
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install -q 2>$null
}
Pop-Location

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "To start the application:" -ForegroundColor Green
Write-Host "`nTerminal 1 (Backend):" -ForegroundColor White
Write-Host "  ./venv/Scripts/Activate.ps1" -ForegroundColor Magenta
Write-Host "  python -m app.main" -ForegroundColor Magenta

Write-Host "`nTerminal 2 (Frontend):" -ForegroundColor White
Write-Host "  cd frontend" -ForegroundColor Magenta
Write-Host "  npm run dev" -ForegroundColor Magenta

Write-Host "`nURLs:" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "  Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Swagger UI: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "`n"
