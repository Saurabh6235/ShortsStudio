@echo off
rem Checks tools, sign-ins, keys and providers (changes nothing)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup\install.ps1" -CheckOnly
echo.
pause
