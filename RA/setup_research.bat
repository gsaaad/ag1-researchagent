@echo off
echo ========================================
echo Research Assistant - Quick Setup
echo ========================================
echo.

echo [1/4] Checking Python...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python 3.8 or higher.
    pause
    exit /b 1
)
echo.

echo [2/4] Installing dependencies...
pip install -r requirements_research.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo.

echo [3/4] Creating logs directory...
if not exist logs mkdir logs
echo Logs directory created.
echo.

echo [4/4] Checking .env file...
if not exist .env (
    echo WARNING: .env file not found!
    echo Creating from .env.example...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env and add your Google API key!
    echo Get your key from: https://makersuite.google.com/app/apikey
    echo.
    pause
) else (
    echo .env file exists.
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To run the application:
echo   python research_main.py
echo.
pause
