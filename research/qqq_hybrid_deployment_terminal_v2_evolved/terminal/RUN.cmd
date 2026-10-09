@echo off
setlocal
cd /d %~dp0
where py >nul 2>nul
if not errorlevel 1 (
  py -3 server.py
  exit /b %errorlevel%
)
where python >nul 2>nul
if errorlevel 1 (
  echo Python 3.10+ not found in PATH.
  pause
  exit /b 1
)
python server.py
