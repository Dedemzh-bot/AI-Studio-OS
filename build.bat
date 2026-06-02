@echo off
title AI Studio OS - Build
echo ========================================
echo   AI Studio OS - PyInstaller Build
echo ========================================
echo.

cd /d "%~dp0"

if not exist "AI_Studio_OS.spec" (
    echo [ERROR] AI_Studio_OS.spec not found!
    pause
    exit /b 1
)

echo [1/3] Cleaning old build artifacts...
if exist "dist\" rmdir /s /q "dist"
if exist "build\" rmdir /s /q "build"

echo [2/3] Building EXE with PyInstaller...
pyinstaller AI_Studio_OS.spec --distpath dist --workpath build --noconfirm
if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo [3/3] Cleaning up build cache...
if exist "build\" rmdir /s /q "build"

echo.
echo ========================================
echo   Build complete!
echo   EXE: dist\AI_Studio_OS_Package.exe
echo ========================================
echo.
echo Copy dist\AI_Studio_OS.exe to test.
echo Development: python server.py
echo.
pause
