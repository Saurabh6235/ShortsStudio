@echo off
rem Shows every job and how far it got
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
py -3.12 -m studio list
echo.
pause
