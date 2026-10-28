@echo off
:: =====================================================================
:: Client Management System - Windows Run Script
:: =====================================================================
:: This script sets up and runs the Client Management System.
:: Steps:
::   1. Checks Python version
::   2. Creates/activates virtual environment
::   3. Installs dependencies
::   4. Copies .env.example to .env if .env doesn't exist
::   5. Runs Alembic database migrations
::   6. Seeds demo data (optional)
::   7. Starts the FastAPI server with uvicorn
:: =====================================================================

setlocal enabledelayedexpansion

:: --- Configuration ---
set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "PYTHON_EXE=python"
set "PIP_EXE=pip"
set "UVICORN_MODULE=app.main:app"
set "HOST=127.0.0.1"
set "PORT=8000"

:: --- Colors ---
set "COLOR_OK=02"
set "COLOR_WARN=06"
set "COLOR_ERR=04"
set "COLOR_INFO=07"

echo.
echo ============================================================================
echo   Client Management System - Startup Script
echo   Version: 0.1.0
echo ============================================================================
echo.

:: --- Change to script directory ---
cd /d "%SCRIPT_DIR%"

:: --- Step 1: Check Python ---
echo [1/7] Checking Python installation...
%PYTHON_EXE% --version >nul 2>&1
if errorlevel 1 (
    color %COLOR_ERR%
    echo ERROR: Python is not installed or not found in PATH.
    echo Please install Python 3.11+ from https://python.org
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('%PYTHON_EXE% --version 2^>^&1') do set "PY_VER=%%v"
echo   Found: %PY_VER%
echo   Working directory: %SCRIPT_DIR%
echo.

:: --- Step 2: Virtual Environment ---
echo [2/7] Setting up virtual environment...
if not exist "%VENV_DIR%" (
    echo   Creating virtual environment at .venv...
    %PYTHON_EXE% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        color %COLOR_ERR%
        echo ERROR: Failed to create virtual environment.
        echo.
        pause
        exit /b 1
    )
    echo   Virtual environment created.
) else (
    echo   Virtual environment already exists.
)

:: Activate virtual environment
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    color %COLOR_ERR%
    echo ERROR: Failed to activate virtual environment.
    echo.
    pause
    exit /b 1
)
echo   Virtual environment activated.
echo.

:: --- Step 3: Install dependencies ---
echo [3/7] Installing dependencies...
%PIP_EXE% install --upgrade pip >nul 2>&1
%PIP_EXE% install -e ".[dev]"
if errorlevel 1 (
    color %COLOR_ERR%
    echo ERROR: Failed to install dependencies.
    echo Check your internet connection and pyproject.toml.
    echo.
    pause
    exit /b 1
)
echo   Dependencies installed.
echo.

:: --- Step 4: Environment configuration ---
echo [4/7] Configuring environment...
if not exist "%SCRIPT_DIR%.env" (
    if exist "%SCRIPT_DIR%.env.example" (
        copy "%SCRIPT_DIR%.env.example" "%SCRIPT_DIR%.env" >nul
        echo   Created .env from .env.example
        echo   Edit .env to customize settings (database, secret key, etc.)
    ) else (
        color %COLOR_WARN%
        echo WARNING: .env.example not found. Using default settings.
    )
) else (
    echo   .env already exists. Skipping copy.
)
echo.

:: --- Step 5: Database migrations ---
echo [5/7] Running database migrations...
call alembic upgrade head
if errorlevel 1 (
    color %COLOR_WARN%
    echo WARNING: Alembic migration failed. You may need to run manually:
    echo   alembic upgrade head
    echo.
) else (
    echo   Database migrations applied successfully.
)
echo.

:: --- Step 6: Seed demo data (optional) ---
echo [6/7] Checking seed data option...
for /f "tokens=1,* delims==" %%a in (%SCRIPT_DIR%.env) do (
    if "%%a"=="SEED_DEMO_DATA" set "SEED_DEMO_DATA=%%b"
)
if /i "!SEED_DEMO_DATA!"=="true" (
    echo   Seeding demo data...
    call python -m app.cli seed
    if errorlevel 1 (
        color %COLOR_WARN%
        echo WARNING: Seeding failed. You may need to run manually:
        echo   python -m app.cli seed
        echo.
    ) else (
        echo   Demo data seeded successfully.
    )
) else (
    echo   Skipping demo data seed (SEED_DEMO_DATA!=true).
)
echo.

:: --- Step 7: Start server ---
echo [7/7] Starting server...
echo   URL: http://%HOST%:%PORT%
echo   API Docs: http://%HOST%:%PORT%/docs
echo   Admin UI: http://%HOST%:%PORT%/ui/
echo   Admin Login: admin@example.com / admin123 (from .env)
echo.
echo   Press Ctrl+C to stop the server.
echo ============================================================================
echo.

call uvicorn %UVICORN_MODULE% --host %HOST% --port %PORT% --reload

:end
endlocal