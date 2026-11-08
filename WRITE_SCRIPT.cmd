@echo off
rem Topic -> script.json + storyboard.md only, to read/edit before spending on voice and rendering
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
py -3.12 -m studio write %*
echo.
pause
