@echo off
rem ---- Enable auto start (creates HKCU Run entry, no admin needed) ----
chcp 65001 >nul
set "PY=D:\tools\anaconda\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%~dp0tools\autostart.py" on
echo.
pause
