@echo off
cd /d "%~dp0"
python -m research.strategy_instance_v1.serve_operator %*
