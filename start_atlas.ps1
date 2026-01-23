# =============================================================================
# Atlas Startup Script - Saudi AI Middleware v2.1
# =============================================================================
# This script starts both the Python backend and React frontend
# Usage: .\start_atlas.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Banner
Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   ATLAS - Saudi AI Middleware v2.1" -ForegroundColor Cyan
Write-Host "   Oracle Connector Lite (Read-Only)" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $SCRIPT_DIR

# Set PYTHONPATH to include src directory
$env:PYTHONPATH = "$SCRIPT_DIR\src"
Write-Host "[OK] PYTHONPATH set to: $env:PYTHONPATH" -ForegroundColor Green

# Check Python
Write-Host ""
Write-Host "[1/4] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "      $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check Node.js
Write-Host "[2/4] Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "      Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Install Python dependencies if needed
Write-Host "[3/4] Installing Python dependencies..." -ForegroundColor Yellow
pip install -q fastapi uvicorn pydantic 2>$null
Write-Host "      Python dependencies ready" -ForegroundColor Green

# Install frontend dependencies
Write-Host "[4/4] Installing frontend dependencies..." -ForegroundColor Yellow
$frontendPath = "$SCRIPT_DIR\src\atlas\frontend"
if (Test-Path "$frontendPath\package.json") {
    Set-Location $frontendPath
    npm install --silent 2>$null
    Set-Location $SCRIPT_DIR
    Write-Host "      Frontend dependencies ready" -ForegroundColor Green
} else {
    Write-Host "[WARN] Frontend package.json not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   Starting Services..." -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Security info
Write-Host "[SECURITY] Oracle Thin Mode: ENABLED" -ForegroundColor Magenta
Write-Host "[SECURITY] Read-Only Mode: ENFORCED" -ForegroundColor Magenta
Write-Host "[SECURITY] DDL/DML Blocked: INSERT, UPDATE, DELETE, DROP, ALTER" -ForegroundColor Magenta
Write-Host ""

# Start Backend (in new window)
Write-Host "[BACKEND] Starting FastAPI on http://localhost:8080" -ForegroundColor Cyan
$backendCmd = "cd '$SCRIPT_DIR'; `$env:PYTHONPATH='$SCRIPT_DIR\src'; python -m uvicorn atlas.api.main:app --host 0.0.0.0 --port 8080 --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

# Wait for backend to start
Start-Sleep -Seconds 3

# Start Frontend (in new window)
Write-Host "[FRONTEND] Starting React on http://localhost:3000" -ForegroundColor Cyan
$frontendCmd = "cd '$frontendPath'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "   Atlas Started Successfully!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "   Backend API:  http://localhost:8080" -ForegroundColor White
Write-Host "   Frontend UI:  http://localhost:3000" -ForegroundColor White
Write-Host "   Health Check: http://localhost:8080/health" -ForegroundColor White
Write-Host "   API Docs:     http://localhost:8080/docs" -ForegroundColor White
Write-Host ""
Write-Host "   Press Ctrl+C in each terminal to stop" -ForegroundColor Gray
Write-Host ""
