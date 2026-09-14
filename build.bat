@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo === Building Sit Reminder exe ===
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found in PATH. Install Python 3.8+ first.
    pause
    exit /b 1
)

python build_exe.py
echo.
pause
