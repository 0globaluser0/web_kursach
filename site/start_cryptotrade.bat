@echo off
cd /d "%~dp0site"
start "CryptoTrade server" cmd /k "python backend.py"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8000/index.html"
