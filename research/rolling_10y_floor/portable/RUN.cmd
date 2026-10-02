@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js 22+ is required.
  exit /b 1
)
node --experimental-strip-types scripts\run-rolling-floor.ts --mode bridge --input-dir inputs\rolling_floor_shards --out-dir output
if errorlevel 1 exit /b %errorlevel%
echo PORTABLE PASS
