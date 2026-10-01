@echo off
setlocal
cd /d "%~dp0"

echo.
echo ============================================
echo QQQ OPERATOR ACCEPTANCE
echo ============================================
echo.

echo [1/2] Compile Python sources...
python -c "import pathlib,py_compile; [py_compile.compile(str(p),doraise=True) for root in ('research/evidence_v1','research/live_hedge_v1','research/strategy_instance_v1') for p in pathlib.Path(root).glob('*.py')]"
if errorlevel 1 (
  echo.
  echo ACCEPTANCE BLOCKED: Python compile failed.
  exit /b 1
)

echo.
echo [2/2] Run evidence + instance tests...
python -m unittest research.evidence_v1.test_evidence research.evidence_v1.test_lock_guard research.strategy_instance_v1.test_instance
if errorlevel 1 (
  echo.
  echo ACCEPTANCE BLOCKED: unittest failed.
  exit /b 1
)

echo.
echo ============================================
echo ACCEPTANCE LOGIC: PASS
echo ============================================
echo.
echo Starting local Operator Console on 127.0.0.1:8766...
start "QQQ Operator Console" /D "%~dp0" cmd /k python -m research.strategy_instance_v1.serve_operator
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8766/research/strategy_instance_v1/operator_dashboard.html"
echo.
echo Browser opened. Console is LOCAL ONLY.
echo Close the Operator Console window to stop the server.
exit /b 0
