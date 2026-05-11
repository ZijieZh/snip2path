@echo off
title Snip2Path Installer
echo ================================
echo   Snip2Path v1.2.1 - Installer
echo ================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+ first.
    echo         https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found

:: Install pip dependencies
echo [*] Installing dependencies...
pip install Pillow -q
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Pillow.
    pause
    exit /b 1
)
echo [OK] Dependencies installed

:: Install snip2path
echo [*] Installing snip2path...
cd /d "%~dp0.."
pip install . -q
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install snip2path.
    pause
    exit /b 1
)
echo [OK] snip2path installed

:: Remove old shortcuts
echo [*] Cleaning up old shortcuts...
del /f /q "%USERPROFILE%\Desktop\Snip2Path.lnk" >nul 2>&1

:: Create desktop shortcuts
echo [*] Creating desktop shortcuts...

:: Snip2Path Background (no window)
powershell -NoProfile -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Snip2Path Background.lnk'); $Shortcut.TargetPath = '%~dp0start-background.bat'; $Shortcut.WorkingDirectory = '%~dp0..'; $Shortcut.IconLocation = 'shell32.dll,13'; $Shortcut.Save()" >nul 2>&1
echo [OK] Snip2Path Background (no window)

:: Stop Snip2Path
powershell -NoProfile -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Stop Snip2Path.lnk'); $Shortcut.TargetPath = '%~dp0stop.bat'; $Shortcut.WorkingDirectory = '%~dp0..'; $Shortcut.IconLocation = 'shell32.dll,28'; $Shortcut.Save()" >nul 2>&1
echo [OK] Stop Snip2Path

echo.
echo ================================
echo   Installation complete!
echo.
echo   Desktop shortcuts created:
echo     - Snip2Path Background: start daemon (no window)
echo     - Stop Snip2Path      : stop daemon
echo   Or run: snip2path --watch
echo ================================
pause
