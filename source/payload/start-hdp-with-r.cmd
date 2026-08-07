@echo off
setlocal
cd /d "%~dp0"
set "HDP_PORT=8080"
if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="HDP_PORT" set "HDP_PORT=%%B"
  )
)
docker compose --profile analytics up -d
if errorlevel 1 (
  echo.
  echo Le demarrage a echoue. Verifiez que Docker Desktop est lance et que le module R a ete installe.
  pause
  exit /b 1
)
start "" "http://localhost:%HDP_PORT%"
