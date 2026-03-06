@echo off
title New Metro Big Bazaar - Offline Setup
color 1F
cls

echo.
echo  ==================================================
echo    New Metro Big Bazaar - Offline Setup
echo  ==================================================
echo.
echo  This will download all required files so the app
echo  works WITHOUT internet connection afterwards.
echo.
echo  You only need to run this ONCE.
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install from python.org
    pause
    exit /b 1
)

:: Install Flask if needed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo  Installing Flask...
    pip install Flask Werkzeug --quiet
)

echo  Downloading offline assets...
echo.
python setup_offline.py

echo.
echo  You can now run START_APP.bat without internet!
echo.
pause
