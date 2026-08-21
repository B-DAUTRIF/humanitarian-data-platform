@echo off
setlocal EnableExtensions DisableDelayedExpansion
title HDP 2.3.2 - Configuration GitHub

echo.
echo ============================================================
echo   Humanitarian Data Platform 2.3.2 - Configuration GitHub
echo ============================================================
echo.
echo Ce correctif enregistre le jeton dans le fichier .env local,
echo recree uniquement le conteneur API et verifie la configuration.
echo Le jeton ne sera ni affiche ni inscrit dans un journal.
echo.

set "HDP_APP=%~1"
if not defined HDP_APP set "HDP_APP=%USERPROFILE%\HumanitarianDataPlatform"

if not exist "%HDP_APP%\compose.yaml" (
  echo Installation introuvable dans :
  echo   %HDP_APP%
  echo.
  set /p "HDP_APP=Chemin complet de l'installation HDP : "
)

if not exist "%HDP_APP%\compose.yaml" (
  call :fail "compose.yaml est introuvable. Aucun fichier n'a ete modifie."
  exit /b 1
)

if not exist "%HDP_APP%\.env" (
  call :fail "Le fichier .env est introuvable. Aucun fichier n'a ete modifie."
  exit /b 1
)

where docker.exe >nul 2>&1
if errorlevel 1 (
  call :fail "Docker est introuvable. Lancez Docker Desktop puis recommencez."
  exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
  call :fail "Docker Desktop ne repond pas. Lancez-le puis recommencez."
  exit /b 1
)

set "HDP_ENV_FILE=%HDP_APP%\.env"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $path=$env:HDP_ENV_FILE; $secure=$null; $ptr=[IntPtr]::Zero; $token=$null; $tmp=$null; try { Write-Host 'Collez un jeton GitHub puis appuyez sur Entree.'; Write-Host 'La saisie est masquee.'; $secure=Read-Host 'Jeton GitHub' -AsSecureString; $ptr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure); $token=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr); if ([string]::IsNullOrWhiteSpace($token)) { throw 'Aucun jeton saisi.' }; if ($token.IndexOfAny([char[]]@([char]13,[char]10)) -ge 0) { throw 'Le jeton contient un retour a la ligne.' }; $lines=[IO.File]::ReadAllLines($path); $out=New-Object 'System.Collections.Generic.List[string]'; $found=$false; foreach ($line in $lines) { if ($line -match '^\s*GITHUB_TOKEN\s*=') { if (-not $found) { [void]$out.Add('GITHUB_TOKEN=' + $token); $found=$true } } else { [void]$out.Add($line) } }; if (-not $found) { [void]$out.Add('GITHUB_TOKEN=' + $token) }; $tmp=Join-Path ([IO.Path]::GetDirectoryName($path)) ([IO.Path]::GetRandomFileName()); [IO.File]::WriteAllLines($tmp,$out,(New-Object Text.UTF8Encoding($false))); [IO.File]::Copy($tmp,$path,$true); Write-Host 'Configuration locale mise a jour.' -ForegroundColor Green } catch { Write-Host ('Echec : ' + $_.Exception.Message) -ForegroundColor Red; exit 1 } finally { if ($tmp -and (Test-Path -LiteralPath $tmp)) { Remove-Item -LiteralPath $tmp -Force }; if ($ptr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }; $token=$null; $secure=$null }"
if errorlevel 1 (
  call :fail "La configuration locale a echoue. Le conteneur API n'a pas ete recree."
  exit /b 1
)

echo.
echo Recreation du conteneur API...
pushd "%HDP_APP%"
docker compose up -d --no-deps --force-recreate api
if errorlevel 1 (
  popd
  call :fail "Docker n'a pas pu recreer l'API. Le jeton reste enregistre dans .env."
  exit /b 1
)

set "HDP_TOKEN_STATUS="
for /f "usebackq delims=" %%S in (`docker compose exec -T api python -c "import os; print('CONFIGURE' if os.getenv('GITHUB_TOKEN', '').strip() else 'ABSENT')" 2^>nul`) do set "HDP_TOKEN_STATUS=%%S"
popd

if /i not "%HDP_TOKEN_STATUS%"=="CONFIGURE" (
  call :fail "L'API ne voit toujours pas GITHUB_TOKEN. Consultez docker compose logs api."
  exit /b 1
)

set "HDP_PORT=8080"
for /f "usebackq tokens=1,* delims==" %%A in ("%HDP_APP%\.env") do (
  if /i "%%A"=="HDP_PORT" set "HDP_PORT=%%B"
)

echo.
echo ============================================================
echo   SUCCES : GITHUB_TOKEN est configure dans l'API.
echo ============================================================
echo.
echo HDP va s'ouvrir. Dans Parametres du projet, la creation du
echo depot GitHub doit maintenant etre disponible.
start "" "http://localhost:%HDP_PORT%"
echo.
pause
exit /b 0

:fail
echo.
echo ECHEC : %~1
echo.
pause
exit /b 0
