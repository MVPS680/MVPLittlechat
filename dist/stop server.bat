@echo off
taskkill /im server.exe /f /t
echo server stopped
timeout /t 3 /nobreak