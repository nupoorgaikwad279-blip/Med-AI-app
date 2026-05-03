@echo off
setlocal
title MedAI Desktop Launcher

echo Starting MedAI Backend Services...
cd /d "%~dp0"

:: Kill any existing instances on port 5000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000') do taskkill /f /pid %%a >nul 2>&1

:: Start the watchdog in the background
start /b "" pythonw run_permanently.py

:: Wait for server to be ready using PowerShell to check port 5000
set "READY=0"
for /L %%i in (1,1,15) do (
    powershell -Command "try { $c = New-Object System.Net.Sockets.TcpClient('127.0.0.1', 5000); if ($c.Connected) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
    if %errorlevel% equ 0 (
        set "READY=1"
        goto :SERVER_READY
    )
    timeout /t 1 /nobreak >nul
)

:SERVER_READY
if "%READY%"=="1" (
    start http://127.0.0.1:5000/
) else (
    :: Fallback if powershell fails
    start http://127.0.0.1:5000/
)

exit
