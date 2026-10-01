@echo off
cd /d "%~dp0"

echo Starting QQQ V22 live strategy observer...
start "QQQ V22 Strategy Watcher" cmd /k python -m research.live_hedge_v1.watch_live_desk --interval 15

echo Starting QQQ strategy dashboard...
start "QQQ V22 Strategy Dashboard" cmd /k python -m research.live_hedge_v1.serve_dashboard

echo Starting QQQ operator console...
start "QQQ V22 Operator Console" cmd /k python -m research.strategy_instance_v1.serve_operator

timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8765/research/live_hedge_v1/dashboard.html"
start "" "http://127.0.0.1:8766/research/strategy_instance_v1/operator_dashboard.html"
