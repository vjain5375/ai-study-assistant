@echo off
title AI Study Assistant
color 0A
echo.
echo ========================================
echo   AI Study Assistant - Starting...
echo ========================================
echo.
echo This window will show the app status.
echo DO NOT CLOSE THIS WINDOW!
echo.
echo The app will open at: http://127.0.0.1:8501
echo.
echo Waiting 5 seconds...
timeout /t 5 /nobreak >nul
echo.
echo Starting Streamlit...
echo.

cd /d "%~dp0"
python -m streamlit run ui/app.py --server.address 127.0.0.1 --server.port 8501

pause

