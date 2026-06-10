@echo off
title Gamma Agent v3.0
color 0A

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║                  GAMMA AGENT v3.0 - AUTONOMOUS AI           ║
echo  ╠══════════════════════════════════════════════════════════════╣
echo  ║  Starting server on http://localhost:5000                   ║
echo  ║  Opening browser automatically...                           ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Please install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if required packages are installed
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install flask flask-cors
)

REM Kill any existing server on port 5000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Start the server in background
start "Gamma Server" python gamma_server.py

REM Wait for server to start
echo Waiting for server to start...
timeout /t 3 /nobreak >nul

REM Open browser
start http://localhost:5000

echo.
echo ✅ Gamma Agent is running!
echo.
echo Open your browser and go to: http://localhost:5000
echo.
echo Press Ctrl+C in this window to stop the server.
echo.

REM Keep window open
pause