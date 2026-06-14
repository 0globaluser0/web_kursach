@echo off
cd /d "%~dp0site"
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8000/index.html'"
python backend.py
pause
