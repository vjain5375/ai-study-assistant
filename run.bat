@echo off
REM Quick launcher for AI Study Assistant
REM Usage: run.bat [host] [port]
REM Example: run.bat localhost 8080

if "%1"=="" set HOST=127.0.0.1
if "%1"=="" goto :default_port
set HOST=%1

:default_port
if "%2"=="" set PORT=8501
if "%2"=="" goto :run
set PORT=%2

:run
echo Starting AI Study Assistant...
echo Host: %HOST%
echo Port: %PORT%
echo.
echo Access the app at: http://%HOST%:%PORT%
echo.

python main.py --host %HOST% --port %PORT%

pause

