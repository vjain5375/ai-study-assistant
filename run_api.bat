@echo off
title FastAPI Backend Server
color 0A
echo.
echo ========================================
echo   FastAPI Backend - Starting...
echo ========================================
echo.
echo The API will be available at:
echo   - API: http://localhost:8000
echo   - Docs: http://localhost:8000/docs
echo   - Health: http://localhost:8000/health
echo.
echo Waiting 3 seconds...
timeout /t 3 /nobreak >nul
echo.
echo Starting FastAPI server...
echo.

cd /d "%~dp0"
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

pause

