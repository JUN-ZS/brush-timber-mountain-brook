@echo off
setlocal
cd /d %~dp0
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -m http.server 8790
  exit /b %errorlevel%
)
where python >nul 2>nul
if errorlevel 1 (
  echo Python 3 not found in PATH.
  pause
  exit /b 1
)
python -m http.server 8790
