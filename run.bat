@echo off
REM DAP Market Research Agent Runner Script for Windows

echo ======================================
echo   DAP Market Research Agent
echo ======================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found!
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Checking dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo Dependencies installed

REM Check if .env file exists
if not exist ".env" (
    echo Warning: .env file not found!
    echo Please create .env file based on .env.example
    echo Would you like to create it now? (y/n)
    set /p response=
    if "%response%"=="y" (
        copy .env.example .env
        echo .env file created. Please edit it with your API keys.
        exit /b 0
    ) else (
        exit /b 1
    )
)

REM Parse command line arguments
set MODE=%1
if "%MODE%"=="" set MODE=once

echo.
echo Running in mode: %MODE%
echo.

REM Run the agent
python -m src.main --mode %MODE%

echo.
echo Done!
pause
