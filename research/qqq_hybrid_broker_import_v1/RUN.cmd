@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage:
  echo   RUN.cmd 2026-09-01 2026-10-06 US America/New_York 0
  echo.
  echo Add CASH=1 as the fifth argument to include account cash-flow history.
  exit /b 2
)
set START=%~1
set END=%~2
set MARKET=%~3
set TZ=%~4
set ACC=%~5
if "%MARKET%"=="" set MARKET=US
if "%TZ%"=="" set TZ=America/New_York
if "%ACC%"=="" set ACC=0
set CASHARG=
if /I "%~6"=="CASH=1" set CASHARG=--with-cashflows
python futu_import.py --start "%START%" --end "%END%" --market "%MARKET%" --timezone "%TZ%" --acc-id "%ACC%" %CASHARG%
endlocal
