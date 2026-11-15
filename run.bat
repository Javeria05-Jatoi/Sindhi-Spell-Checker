@echo off
rem Starts the web app and opens http://localhost:8000 in the browser.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run setup.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\serve.py
pause
