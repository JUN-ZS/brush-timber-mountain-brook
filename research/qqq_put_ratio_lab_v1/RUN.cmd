@echo off
setlocal
cd /d "%~dp0"
echo QQQ Put Ratio Research Lab - local only, no broker connection
echo Open http://127.0.0.1:8765/ in your browser.
start "" http://127.0.0.1:8765/
python -m http.server 8765 --bind 127.0.0.1
