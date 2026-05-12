@echo off
chcp 65001 > nul

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Installing Python 3.12...
    winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
    
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
    timeout /t 5 /nobreak > nul
    
    python --version >nul 2>&1
    if errorlevel 1 (
        echo Python install failed. Install manually from python.org
        pause
        exit /b 1
    )
)

REM Create venv
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Install requirements
echo Installing requirements...
call venv\Scripts\pip install -r requirements.txt >nul 2>&1

REM Run hidden
echo Starting system hidden...
wscript //nologo run_hidden.vbs

REM Exit immediately
exit
