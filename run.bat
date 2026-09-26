@echo off
REM Starts the Spendly app at http://127.0.0.1:5001
REM Creates the venv and installs dependencies on first run.

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv || goto :error
)

venv\Scripts\python.exe -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    venv\Scripts\python.exe -m pip install -r requirements.txt || goto :error
)

echo Starting Spendly at http://127.0.0.1:5001 (Ctrl+C to stop)
venv\Scripts\python.exe app.py
goto :eof

:error
echo.
echo Setup failed - see the messages above.
pause
exit /b 1
