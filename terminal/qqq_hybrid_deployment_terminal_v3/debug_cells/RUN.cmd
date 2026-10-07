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
  echo   RUN.cmd ALL
  exit /b 2
)
if /I "%~1"=="ALL" (
  for %%N in (01 02 03 04 05 06) do (
    echo.
    echo ===== CELL %%N =====
    node cell%%N_*.js
    if errorlevel 1 exit /b 1
  )
  exit /b 0
)
set CELL=%~1
if "%CELL%"=="1" set CELL=01
if "%CELL%"=="2" set CELL=02
if "%CELL%"=="3" set CELL=03
if "%CELL%"=="4" set CELL=04
if "%CELL%"=="5" set CELL=05
if "%CELL%"=="6" set CELL=06
node cell%CELL%_*.js
endlocal
