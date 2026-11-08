@echo off
rem Every .txt in inbox (each may hold several topics) -> finished videos, one after another
cd /d "%~dp0"
set CI=1
set PYTHONIOENCODING=utf-8
set HEYGEN_NO_ANALYTICS=1
py -3.12 -m studio make --all %*
echo.
pause
