@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage:
  echo   RUN.cmd C:\path\to\broker_import_2026-09-01_2026-10-06.json 123456
  echo   RUN.cmd C:\path\to\broker_import_2026-09-01_2026-10-06.json 123456 OPENING_CASH=50000
  echo.
  echo This performs read-only OpenD REAL position/funds reconciliation.
  exit /b 2
)
set INPUT=%~1
set ACC=%~2
set OPENING=
if /I not "%~3"=="" if /I "%~3:~0,13%"=="OPENING_CASH=" set OPENING=%~3:~13%
if "%ACC%"=="" set ACC=0
set OPENING_ARG=
if not "%OPENING%"=="" set OPENING_ARG=--opening-cash "%OPENING%"
python broker_reconcile.py --input "%INPUT%" --acc-id "%ACC%" %OPENING_ARG%
endlocal
