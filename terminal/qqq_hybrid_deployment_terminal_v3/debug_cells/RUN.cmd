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
  echo   RUN.cmd 9
  echo   RUN.cmd 10
  echo   RUN.cmd 11
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
  if errorlevel 1 exit /b 1
  call :cell 9
  if errorlevel 1 exit /b 1
  call :cell 10
  if errorlevel 1 exit /b 1
  call :cell 11
  exit /b %errorlevel%
)
call :cell %~1
exit /b %errorlevel%

:cell
set CELL=%~1
if "%CELL%"=="1" (
  node cell01_operator_input.js
  exit /b %errorlevel%
)
if "%CELL%"=="2" (
  node cell02_decision.js
  exit /b %errorlevel%
)
if "%CELL%"=="3" (
  node cell03_operator_current.js
  exit /b %errorlevel%
)
if "%CELL%"=="4" (
  node cell04_candidate.js
  exit /b %errorlevel%
)
if "%CELL%"=="5" (
  node cell05_build.js
  exit /b %errorlevel%
)
if "%CELL%"=="6" (
  node cell06_watch.js
  exit /b %errorlevel%
)
if "%CELL%"=="7" (
  node cell07_operator_summary.js
  exit /b %errorlevel%
)
if "%CELL%"=="8" (
  node cell08_current_option_leg.js
  exit /b %errorlevel%
)
if "%CELL%"=="9" (
  python cell09_delayed_data.py
  exit /b %errorlevel%
)
if "%CELL%"=="10" (
  python cell10_option_candidate_retrieval.py
  exit /b %errorlevel%
)
if "%CELL%"=="11" (
  python cell11_opend_option_fallback.py
  exit /b %errorlevel%
)
echo Unknown cell: %CELL%
exit /b 2
