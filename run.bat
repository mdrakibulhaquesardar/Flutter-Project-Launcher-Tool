@echo off
echo Starting FluStudio...
echo.

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo Error: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

REM Run the application
venv\Scripts\python.exe main.py

