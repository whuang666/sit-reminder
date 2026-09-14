@echo off
rem ---- Disable auto start (removes HKCU Run entry) ----
chcp 65001 >nul
set "PY=D:\tools\anaconda\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%~dp0tools\autostart.py" off
echo.
pause
