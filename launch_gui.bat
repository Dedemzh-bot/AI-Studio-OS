@echo off
title AI Studio OS
echo 🎮 AI Studio OS v2
echo.
echo Starting engine and opening browser...
echo.

cd /d "%~dp0"

start /min python server.py
timeout /t 2 /nobreak >nul
start http://localhost:8080

echo.
echo Server running at http://localhost:8080
echo Close this window to stop the server.
pause >nul
