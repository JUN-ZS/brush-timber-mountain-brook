@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage:
  echo   RUN.cmd 1-19
  echo   RUN.cmd ALL
  echo   RUN.cmd 17-demo
  echo   RUN.cmd 17-selftest
  exit /b 2
)
if /I "%~1"=="ALL" (
  for %%C in (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 18 19) do (
    call :cell %%C
    if errorlevel 1 exit /b 1
  )
  call :cell 17self
  exit /b %errorlevel%
)
if /I "%~1"=="17-demo" goto cell17demo
if /I "%~1"=="17-selftest" goto cell17self
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
if "%CELL%"=="18" (
  node cell18_web_beginner_input.js
  exit /b %errorlevel%
)
if "%CELL%"=="19" (
  node cell19_data_gate_dates.js
  exit /b %errorlevel%
)
if "%CELL%"=="17" (
  node cell17_beginner_guided_input.js
  exit /b %errorlevel%
)
echo Unknown cell: %CELL%
exit /b 2

:cell17demo
node cell17_beginner_guided_input.js --demo
exit /b %errorlevel%

:cell17self
node cell17_beginner_guided_input.js --self-test
exit /b %errorlevel%
