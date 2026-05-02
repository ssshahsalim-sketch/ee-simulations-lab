@echo off
title EE Simulations Server
echo ============================================================
echo   ⚡ EE Simulations Lab - Starting Server
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install from python.org
    pause & exit /b 1
)

echo [INFO] Installing required libraries...
python -m pip install flask --quiet
echo [OK] Flask ready

echo.
echo ============================================================
echo   Server starting...
echo.
echo   Local site:  http://localhost:5000
echo   Admin panel: http://localhost:5000/admin
echo   Password:    admin123  (change in app.py)
echo.
echo   Put your .html simulation files in the "simulations" folder
echo   They will appear on the site automatically!
echo ============================================================
echo.
echo   Press Ctrl+C to stop the server
echo.

python app.py
pause
