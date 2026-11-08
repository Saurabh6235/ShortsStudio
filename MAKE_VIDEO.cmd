@echo off
rem Topic file(s) in inbox -> finished videos. One file can hold several topics separated by a line of ---
cd /d "%~dp0"
set CI=1
set PYTHONIOENCODING=utf-8
set HEYGEN_NO_ANALYTICS=1
py -3.12 -m studio make %*
echo.
pause
