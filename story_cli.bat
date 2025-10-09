@echo off
REM AI Story Agent CLI - Windows Batch Wrapper
REM Usage: story_cli.bat [options]

setlocal enabledelayedexpansion

REM Default values
set API_URL=http://localhost:8000
set API_MODE=false
set API_TOKEN=

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :main
if "%~1"=="--api" (
    set API_MODE=true
    shift
    goto :parse_args
)
if "%~1"=="--url" (
    set API_URL=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--token" (
    set API_TOKEN=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--help" (
    goto :show_help
)
if "%~1"=="-h" (
    goto :show_help
)

REM Pass remaining arguments to Python
set PYTHON_ARGS=%*
goto :main

:show_help
echo AI Story Agent CLI - Windows Batch Wrapper
echo.
echo Usage: %~nx0 [OPTIONS]
echo.
echo Options:
echo   --api              Use API backend mode
echo   --url URL          API backend URL (default: http://localhost:8000)
echo   --token TOKEN      API authentication token
echo   --help, -h         Show this help message
echo.
echo Examples:
echo   %~nx0                                    # Interactive mode (standalone)
echo   %~nx0 --api                             # Interactive mode (API backend)
echo   %~nx0 --api --create "My Adventure"     # Create new session via API
echo.
goto :end

:main
echo [GAME] AI Story Agent CLI
echo ========================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Error: Python is not installed or not in PATH
    goto :end
)

REM Build Python command
set PYTHON_CMD=python cli.py

if "%API_MODE%"=="true" (
    set PYTHON_CMD=!PYTHON_CMD! --api --api-url %API_URL%
    if not "%API_TOKEN%"=="" (
        set PYTHON_CMD=!PYTHON_CMD! --api-token %API_TOKEN%
    )
)

if not "%PYTHON_ARGS%"=="" (
    set PYTHON_CMD=!PYTHON_CMD! %PYTHON_ARGS%
)

REM Execute Python command
echo Running: !PYTHON_CMD!
echo.
!PYTHON_CMD!

:end
pause
