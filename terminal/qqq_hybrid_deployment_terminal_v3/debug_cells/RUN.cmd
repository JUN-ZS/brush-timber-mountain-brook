@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage:
  echo   RUN.cmd 1
  echo   RUN.cmd 2
  echo   RUN.cmd 3
  echo   RUN.cmd 4
  echo   RUN.cmd 5
  echo   RUN.cmd 6
  echo   RUN.cmd 7
  echo   RUN.cmd 8
  echo   RUN.cmd ALL
  exit /b 2
)
if /I "%~1"=="ALL" (
  call :cell 1
  if errorlevel 1 exit /b 1
  call :cell 2
  if errorlevel 1 exit /b 1
  call :cell 3
  if errorlevel 1 exit /b 1
  call :cell 4
  if errorlevel 1 exit /b 1
  call :cell 5
  if errorlevel 1 exit /b 1
  call :cell 6
  if errorlevel 1 exit /b 1
  call :cell 7
  if errorlevel 1 exit /b 1
  call :cell 8
  exit /b %errorlevel%
)
call :cell %~1
exit /b %errorlevel%

:cell
set CELL=%~1
if "%CELL%"=="1" node cell01_operator_input.js
if "%CELL%"=="2" node cell02_decision.js
if "%CELL%"=="3" node cell03_operator_current.js
if "%CELL%"=="4" node cell04_candidate.js
if "%CELL%"=="5" node cell05_build.js
if "%CELL%"=="6" node cell06_watch.js
if "%CELL%"=="7" node cell07_operator_summary.js
if "%CELL%"=="9" python cell09_delayed_data.py
if "%CELL%"=="8" node cell08_current_option_leg.js
if not "%CELL%"=="1" if not "%CELL%"=="2" if not "%CELL%"=="3" if not "%CELL%"=="4" if not "%CELL%"=="5" if not "%CELL%"=="6" if not "%CELL%"=="7" if not "%CELL%"=="8" (
  echo Unknown cell: %CELL%
  exit /b 2
)
exit /b 0
