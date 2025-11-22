@echo off
REM Build installer script for FluStudio
echo ========================================
echo Building FluStudio Installer
echo ========================================
echo.

REM Check if EXE exists
if not exist "dist\FluStudio\FluStudio.exe" (
    echo ERROR: Executable not found!
    echo Please run build.bat first to create the executable.
    pause
    exit /b 1
)

REM Check if Inno Setup is installed
set "INNO_SETUP_PATH="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "INNO_SETUP_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "INNO_SETUP_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
) else (
    echo.
    echo ERROR: Inno Setup not found!
    echo.
    echo Please install Inno Setup from:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo Or manually compile build_installer.iss using Inno Setup Compiler.
    echo.
    pause
    exit /b 1
)

echo Found Inno Setup at: %INNO_SETUP_PATH%
echo.

REM Create installer output directory
if not exist "dist\installer" mkdir "dist\installer"

echo Compiling installer...
"%INNO_SETUP_PATH%" build_installer.iss

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Installer created successfully!
    echo ========================================
    echo.
    echo Installer location: dist\installer\FluStudio-Setup-1.0.1.exe
    echo.
) else (
    echo.
    echo ========================================
    echo Installer creation failed!
    echo ========================================
    exit /b 1
)

pause

