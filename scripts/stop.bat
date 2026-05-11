@echo off
title Snip2Path Stopper

taskkill /f /im pythonw.exe >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Snip2Path Background stopped
) else (
    echo Snip2Path Background was not running
)

timeout /t 1 >nul
