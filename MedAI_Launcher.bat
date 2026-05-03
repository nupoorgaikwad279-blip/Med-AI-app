@echo off
setlocal
title MedAI Desktop Launcher

echo ============================================================
echo           MEDAI HEALTHCARE AI - DESKTOP LAUNCHER
echo ============================================================
echo.

:: Set paths
set APP_DIR=%~dp0
set APP_SCRIPT=app.py
set WATCHDOG_SCRIPT=run_permanently.py

cd /d "%APP_DIR%"

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python to run this application.
    pause
    exit /b 1
)

:: Kill any existing instances on port 5000 (optional but recommended for stability)
echo [*] Cleaning up existing sessions...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000') do taskkill /f /pid %%a >nul 2>&1

:: Start the watchdog/server in the background
echo [*] Starting MedAI Backend Services...
start /b "" pythonw "%WATCHDOG_SCRIPT%"

:: Wait for server to be ready using PowerShell to check port 5000
echo [*] Waiting for server to initialize (this may take a few seconds)...
set "READY=0"
for /L %%i in (1,1,10) do (
    powershell -Command "try { $c = New-Object System.Net.Sockets.TcpClient('127.0.0.1', 5000); if ($c.Connected) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
    if %errorlevel% equ 0 (
        set "READY=1"
        goto :SERVER_READY
    )
    echo     [Attempt %%i] Server not ready yet...
    timeout /t 2 /nobreak >nul
)

:SERVER_READY
if "%READY%"=="1" (
    echo.
    echo [SUCCESS] MedAI Server is online!
    echo [*] Launching Desktop Interface...
    start http://127.0.0.1:5000/
) else (
    echo.
    echo [WARNING] Server initialization is taking longer than expected.
    echo Attempting to open browser anyway...
    timeout /t 3 /nobreak >nul
    start http://127.0.0.1:5000/
)

echo.
echo ============================================================
echo  MedAI is now running in the background.
echo  You can safely close this window.
echo ============================================================
timeout /t 3 >nul
exit
