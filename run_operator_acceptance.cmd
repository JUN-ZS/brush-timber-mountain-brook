@echo off
setlocal
cd /d "%~dp0"

echo.
echo ============================================
echo QQQ OPERATOR ACCEPTANCE
echo ============================================
echo.

echo [1/5] Compile Python sources...
python -c "import pathlib,py_compile; [py_compile.compile(str(p),doraise=True) for root in ('research/evidence_v1','research/live_hedge_v1','research/strategy_instance_v1') for p in pathlib.Path(root).glob('*.py')]"
if errorlevel 1 (
  echo.
  echo ACCEPTANCE BLOCKED: Python compile failed.
  exit /b 1
)

echo.
echo [2/5] Run evidence + instance tests...
python -m unittest research.evidence_v1.test_evidence research.evidence_v1.test_lock_guard research.strategy_instance_v1.test_instance
if errorlevel 1 (
  echo.
  echo ACCEPTANCE BLOCKED: unittest failed.
  exit /b 1
)

echo.
echo [3/5] Check operator UI wiring and safety boundaries...
python -c "from pathlib import Path; d=Path('research/strategy_instance_v1/operator_dashboard.html').read_text(encoding='utf-8'); s=Path('research/strategy_instance_v1/serve_operator.py').read_text(encoding='utf-8'); r=Path('research/strategy_instance_v1/run_instance.py').read_text(encoding='utf-8'); l=Path('research/live_hedge_v1/run_live_desk.py').read_text(encoding='utf-8'); assert 'state.performance_tape' in d; assert 'exportTapeCsv' in d; assert '127.0.0.1' in s and 'place_order' not in s and 'modify_order' not in s; assert 'build_performance_tape' in r; assert 'strategy_leg_action' in l and 'direction' in l"
if errorlevel 1 (
  echo.
  echo ACCEPTANCE BLOCKED: UI wiring or safety check failed.
  exit /b 1
)

echo.
echo [4/5] Check DESK/AUDIT exclusivity...
python research\strategy_instance_v1\check_operator_acceptance_ui.py exclusivity
if errorlevel 1 (
  echo.
  echo ACCEPTANCE BLOCKED: DESK/AUDIT check failed.
  exit /b 1
)

echo.
echo [5/5] Check live-position Gap semantics...
python research\strategy_instance_v1\check_operator_acceptance_ui.py gap
if errorlevel 1 (
  echo.
  echo ACCEPTANCE BLOCKED: Gap semantics check failed.
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
