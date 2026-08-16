@echo off
setlocal
cd /d "%~dp0"
set "HDP_PORT=8080"
set "HDP_LOCAL_TOKEN="
if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="HDP_PORT" set "HDP_PORT=%%B"
    if /i "%%A"=="HDP_LOCAL_TOKEN" set "HDP_LOCAL_TOKEN=%%B"
  )
)
docker compose up -d
if errorlevel 1 (
  echo.
  echo Le demarrage a echoue. Verifiez que Docker Desktop est lance.
  pause
  exit /b 1
)
if not defined HDP_LOCAL_TOKEN (
  echo Jeton local HDP absent. Relancez l'installateur V5 pour reparer .env.
  pause
  exit /b 1
)
start "" "http://localhost:%HDP_PORT%/?token=%HDP_LOCAL_TOKEN%"
