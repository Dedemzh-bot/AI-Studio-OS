@echo off
echo 🎮 AI Studio OS - Web GUI Launcher
echo.
echo Starting Streamlit server at http://localhost:8501
echo The web page will open automatically in your browser.
echo Press Ctrl+C in this window to stop.
echo.
cd /d "%~dp0"
streamlit run app.py --server.headless true
