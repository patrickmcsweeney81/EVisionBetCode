@echo off
setlocal enabledelayedexpansion

REM Change to script directory (handles spaces in path)
cd /d "%~dp0"

REM Parse args for telegram toggle
set TELEGRAM_ENABLED=%TELEGRAM_ENABLED%
for %%A in (%*) do (
    if /I "%%~A"=="--no-telegram" set TELEGRAM_ENABLED=0
    if /I "%%~A"=="--telegram-off" set TELEGRAM_ENABLED=0
    if /I "%%~A"=="--telegram-on" set TELEGRAM_ENABLED=1
)

REM Prefer local venv python if present
set PY_EXE=.venv\Scripts\python.exe
if not exist "%PY_EXE%" (
    set PY_EXE=python
)

echo Running with TELEGRAM_ENABLED=%TELEGRAM_ENABLED%
"%PY_EXE%" ev_arb_bot.py

endlocal
@echo off
REM launcher.bat - simple launcher for EV Bot (EV-only; arbitrage removed)
REM Usage: launcher.bat [args...]  (args forwarded to ev_arb_bot.py)

setlocal enabledelayedexpansion

:: Ensure we run from script directory
cd /d "%~dp0"

:: Check for Python
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH. Install Python 3.8+ and retry.
    exit /b 1
)

:: Create a virtual environment if none exists
if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment (.venv)...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        exit /b 1
    )
)

:: Activate virtual environment
call ".venv\Scripts\activate.bat"

:: Install dependencies if requirements.txt exists
if exist "requirements.txt" (
    echo Installing Python dependencies from requirements.txt...
    pip install --upgrade pip >nul
    pip install -r requirements.txt
)

:: Ensure data directory exists (per project conventions)
if not exist "data" mkdir "data"

:: Run the bot and forward any arguments. Keep console open for output.
echo Starting EV Bot (EV-only mode)...
python ev_arb_bot.py %*

:: Optional: keep the window open if launched by double-click
if "%~1"=="" (
    echo.
    echo Press any key to exit...
    pause >nul
)

endlocal