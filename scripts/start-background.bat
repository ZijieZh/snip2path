@echo off
title Snip2Path Background

:: Find pythonw.exe in the same directory as python.exe
for %%I in (python.exe) do set PYTHON_DIR=%%~dp$PATH:I
if defined PYTHON_DIR (
    set PYTHONW=%PYTHON_DIR%pythonw.exe
) else (
    set PYTHONW=pythonw
)

"%PYTHONW%" -m snip2path --watch --silent
