@echo off
setlocal
cd /d "%~dp0"
docker compose --profile analytics down
if errorlevel 1 pause
