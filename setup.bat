@echo off
rem One-time setup on Windows: creates .venv, installs packages, downloads the translator.
setlocal
cd /d "%~dp0"
echo.
echo === Sindhi Spell-Checker: setup ===
echo.

set "PY="
for %%v in (3.12 3.13 3.11 3.14) do (
  if not defined PY (
    py -%%v -c "import sys" >nul 2>&1 && set "PY=py -%%v"
  )
)
if not defined PY (
  python -c "import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,14) else 1)" >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo Python 3.11 to 3.14 was not found.
  echo Install Python 3.12 from https://www.python.org/downloads/
  echo and tick "Add python.exe to PATH" during install. Then run setup.bat again.
  pause
  exit /b 1
)
echo Using: %PY%

if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Creating virtual environment .venv
  %PY% -m venv .venv || goto :fail
) else (
  echo [1/3] .venv already exists
)

echo [2/3] Installing packages (a few minutes the first time)
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :fail
echo Unpacking the data files
".venv\Scripts\python.exe" -c "import src; print('Data files ready.')" || goto :fail

echo [3/3] Downloading the offline translator model (about 630 MB)
".venv\Scripts\python.exe" scripts\download_models.py
if errorlevel 1 (
  echo.
  echo The translator download failed. The app still works; the Translate tab
  echo will use dictionary glosses. Run setup.bat again later to retry.
)

echo.
echo === Setup finished. Double-click run.bat to start the app. ===
pause
exit /b 0

:fail
echo.
echo Setup failed. Check your internet connection and the messages above, then run setup.bat again.
pause
exit /b 1
