@echo off
cd /d "%~dp0"
echo AI Studio OS - Web Console
echo.
echo Opening http://localhost:8501 ...
echo Press Ctrl+C to stop.
echo.
echo. | streamlit run app.py
pause
