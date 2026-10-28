@echo off
:: =====================================================================
:: Client Management System - Installation Script
:: =====================================================================
:: This script sets up the Client Management System for first-time use.
:: Steps:
::   1. Checks Python version
::   2. Creates/activates virtual environment
::   3. Installs dependencies
::   4. Copies .env.example to .env if .env doesn't exist
::   5. Runs Alembic database migrations
::   6. Seeds demo data
:: =====================================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "PYTHON_EXE=python"
set "PIP_EXE=pip"

set "COLOR_OK=02"
set "COLOR_WARN=06"
set "COLOR_ERR=04"
set "COLOR_INFO=07"

echo.
echo ============================================================================
echo   Client Management System - Installation Script
echo   Version: 0.1.0
echo ============================================================================
echo.

cd /d "%SCRIPT_DIR%"

echo [1/6] Checking Python installation...
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
echo.

echo [2/6] Setting up virtual environment...
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

echo [3/6] Installing dependencies...
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

echo [4/6] Configuring environment...
if not exist "%SCRIPT_DIR%.env" (
    if exist "%SCRIPT_DIR%.env.example" (
        copy "%SCRIPT_DIR%.env.example" "%SCRIPT_DIR%.env" >nul
        echo   Created .env from .env.example
        echo   Edit .env to customize settings.
    ) else (
        color %COLOR_WARN%
        echo WARNING: .env.example not found.
    )
) else (
    echo   .env already exists.
)
echo.

echo [5/6] Running database migrations...
call alembic upgrade head
if errorlevel 1 (
    color %COLOR_WARN%
    echo WARNING: Migration failed. Run manually: alembic upgrade head
) else (
    echo   Migrations applied successfully.
)
echo.

echo [6/6] Seeding demo data...
call python -m app.cli seed
if errorlevel 1 (
    color %COLOR_WARN%
    echo WARNING: Seeding failed. Run manually: python -m app.cli seed
) else (
    echo   Demo data seeded successfully.
)
echo.

color %COLOR_OK%
echo ============================================================================
echo   Installation complete!
echo   To start the server: run.bat
echo   API Docs: http://127.0.0.1:8000/docs
echo   Admin UI: http://127.0.0.1:8000/ui/
echo   Admin Login: admin@example.com / admin123
echo ============================================================================
echo.

endlocal