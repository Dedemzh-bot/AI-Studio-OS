@echo off
title AI Studio OS
echo AI Studio OS v2 - FastAPI + WebSocket
echo.
cd /d "%~dp0"
start http://localhost:8080
python -m uvicorn server:app --host 0.0.0.0 --port 8080 --log-level warning
pause
