@echo off
REM Build script for FluStudio EXE
echo ========================================
echo Building FluStudio Executable
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo Virtual environment not found. Creating...
    python -m venv venv
    echo Installing dependencies...
    venv\Scripts\python.exe -m pip install --upgrade pip
    venv\Scripts\python.exe -m pip install -r requirements.txt
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo.
echo Building executable with PyInstaller...
pyinstaller build_exe.spec --clean --noconfirm

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Build completed successfully!
    echo ========================================
    echo.
    echo Executable location: dist\FluStudio\FluStudio.exe
    echo.
    echo To create installer, run: build_installer.bat
) else (
    echo.
    echo ========================================
    echo Build failed!
    echo ========================================
    exit /b 1
)

pause

