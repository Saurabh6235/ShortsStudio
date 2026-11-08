@echo off
rem Run or resume one job: BUILD_VIDEO.cmd <job> [--from STAGE]   (job = folder name in jobs\)
cd /d "%~dp0"
set CI=1
set PYTHONIOENCODING=utf-8
set HEYGEN_NO_ANALYTICS=1
set JOB=%1
if "%JOB%"=="" set /p JOB=Job name (folder in jobs\): 
py -3.12 -m studio build %JOB% %2 %3
echo.
pause
