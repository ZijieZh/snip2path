@echo off
title Snip2Path Installer
echo ================================
echo   Snip2Path v1.0.0 - Installer
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

:: Create desktop shortcut
echo [*] Creating desktop shortcut...
powershell -Command "
\$WshShell = New-Object -ComObject WScript.Shell
\$Shortcut = \$WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\\Snip2Path.lnk')
\$Shortcut.TargetPath = '%~dp0start.bat'
\$Shortcut.WorkingDirectory = '%~dp0..'
\$Shortcut.IconLocation = 'shell32.dll,13'
\$Shortcut.Save()
" >nul 2>&1
echo [OK] Desktop shortcut created: Snip2Path

echo.
echo ================================
echo   Installation complete!
echo.
echo   Double-click "Snip2Path" on your desktop to start.
echo   Or run: snip2path --watch
echo ================================
pause
