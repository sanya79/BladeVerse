@echo off
REM ============================================================================
REM Fruit Ninja - Game Setup Script for Windows
REM ============================================================================
REM This script sets up the virtual environment and installs all dependencies

echo.
echo ============================================================================
echo FRUIT NINJA - Setup Script
echo ============================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/3] Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip setuptools wheel >nul 2>&1

REM Install requirements
pip install -r "requirements (1).txt"
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo SETUP COMPLETE!
echo ============================================================================
echo.
echo To run the game:
echo   1. Open a terminal in this folder
echo   2. Run: venv\Scripts\activate
echo   3. Run: python main.py
echo.
echo Keyboard Controls:
echo   ESC         - Pause/Unpause game
echo   F3          - Toggle FPS counter
echo   F4          - Toggle debug mode (hand landmarks)
echo   F11         - Toggle fullscreen
echo.
echo Optional: Add fonts from fonts.google.com to assets/fonts/
echo Optional: Add .ogg sound files to assets/sounds/
echo.
pause
