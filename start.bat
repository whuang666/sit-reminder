@echo off
rem ============================================================
rem  Sit Reminder launcher   (ASCII only - do not add CJK here)
rem  Prefers pythonw.exe so that no console window shows up.
rem ============================================================
chcp 65001 >nul
setlocal
set "SCRIPT=%~dp0water_break_reminder.py"
set "PYW="

rem 1) pythonw.exe from PATH
for %%C in (pythonw.exe) do if not defined PYW set "PYW=%%~$PATH:C"

rem 2) the "py" launcher in windowed mode
if not defined PYW (
  for %%C in (pyw.exe) do if not defined PYW set "PYW=%%~$PATH:C"
)

rem 3) well-known install locations
if not defined PYW if exist "%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe" set "PYW=%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe"
if not defined PYW if exist "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" set "PYW=%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
if not defined PYW if exist "%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe" set "PYW=%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe"
if not defined PYW if exist "C:\Python313\pythonw.exe" set "PYW=C:\Python313\pythonw.exe"

if not defined PYW (
  echo.
  echo   pythonw.exe was not found on this machine.
  echo   Please install Python 3.10+ from https://www.python.org/downloads/
  echo   and tick "Add python.exe to PATH" during setup.
  echo.
  pause
  exit /b 1
)

start "" "%PYW%" "%SCRIPT%"
