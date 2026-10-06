@echo off
setlocal
cd /d %~dp0

where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher "py" not found.
  exit /b 1
)

py -3 collect_delayed_vx_m1_m2.py --out delayed_vx_m1_m2.json
if errorlevel 1 (
  echo.
  echo Cboe delayed VX snapshot FAILED.
  exit /b %errorlevel%
)

echo.
echo Wrote: %cd%\delayed_vx_m1_m2.json