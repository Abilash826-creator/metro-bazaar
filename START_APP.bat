@echo off
title New Metro Big Bazaar - Billing System
color 1F
cls

echo.
echo  ==================================================
echo    New Metro Big Bazaar - Billing ^& Inventory
echo  ==================================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed!
    echo.
    echo  Please install Python 3.8 or higher from:
    echo  https://www.python.org/downloads/
    echo.
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

:: Check Flask is installed, install if missing
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo  Flask not found. Installing required packages...
    echo.
    pip install Flask Werkzeug --quiet
    if errorlevel 1 (
        echo  [ERROR] Could not install Flask.
        echo  Please run: pip install Flask Werkzeug
        pause
        exit /b 1
    )
    echo  Packages installed successfully!
    echo.
)

echo  Starting New Metro Big Bazaar...
echo  The app will open in your browser automatically.
echo.
echo  Login credentials:  admin / admin123
echo.
echo  DO NOT close this window while using the app.
echo  Close this window to stop the application.
echo  --------------------------------------------------
echo.

:: Run the launcher
python launcher.py

echo.
echo  Application stopped.
pause
