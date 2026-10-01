@echo off
cd /d "%~dp0"
start "QQQ Strategy Operator Server" cmd /k python -m research.strategy_instance_v1.serve_operator %*
start "" "http://127.0.0.1:8766/research/strategy_instance_v1/operator_dashboard.html"
