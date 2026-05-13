@echo off
:: AI Studio OS — 主路由启动脚本
:: 使用 py 启动器绕过 Windows Store 占位程序，确保调用真正的 Python
cd /d "%~dp0"
py -3 main_router.py
pause
