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
  echo   RUN.cmd 12
  echo   RUN.cmd 13
  echo   RUN.cmd 14
  echo   RUN.cmd 15
  echo   RUN.cmd 16
  echo   RUN.cmd 17
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
  if errorlevel 1 exit /b 1
  call :cell 12
  if errorlevel 1 exit /b 1
  call :cell 13
  if errorlevel 1 exit /b 1
  call :cell 14
  if errorlevel 1 exit /b 1
  call :cell 15
  if errorlevel 1 exit /b 1
  call :cell 16
  if errorlevel 1 exit /b 1
  call :cell 17
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
if "%CELL%"=="12" (
  node cell12_journal_contract.js
  exit /b %errorlevel%
)
if "%CELL%"=="13" (
  node cell13_operator_clarity.js
  exit /b %errorlevel%
)
if "%CELL%"=="14" (
  node cell14_journal_memory.js
  exit /b %errorlevel%
)
if "%CELL%"=="15" (
  node cell15_strategy_funding_context.js
  exit /b %errorlevel%
)
if "%CELL%"=="16" (
  node cell16_strategy_action_bridge.js
  exit /b %errorlevel%
)
if "%CELL%"=="17" (
  node cell17_beginner_guided_input.js --self-test
  exit /b %errorlevel%
)
echo Unknown cell: %CELL%
exit /b 2
