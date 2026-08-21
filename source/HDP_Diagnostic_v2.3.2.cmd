@echo off
setlocal EnableExtensions DisableDelayedExpansion

for /f "usebackq delims=" %%D in (`powershell.exe -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "HDP_DESKTOP=%%D"
for /f "usebackq delims=" %%T in (`powershell.exe -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"`) do set "HDP_STAMP=%%T"

set "HDP_LOG=%HDP_DESKTOP%\HDP_Debug_v2.3.2_%HDP_STAMP%.log"
set "HDP_APP=%USERPROFILE%\HumanitarianDataPlatform"
set "HDP_INSTALLER_LOGS=%LOCALAPPDATA%\HumanitarianDataPlatform\logs"
set "HDP_RUN_CWD=%CD%"

call :log "Humanitarian Data Platform 2.3.2 - diagnostic borne"
call :log "Date locale : %date% %time%"
call :log "Utilisateur : %USERNAME%"
call :log "Ordinateur : %COMPUTERNAME%"
call :log "Architecture : %PROCESSOR_ARCHITECTURE%"

>>"%HDP_LOG%" echo.
>>"%HDP_LOG%" echo [Windows]
ver >>"%HDP_LOG%" 2>&1
powershell.exe -NoProfile -Command "Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture | Format-List" >>"%HDP_LOG%" 2>&1

>>"%HDP_LOG%" echo.
>>"%HDP_LOG%" echo [Espace disque]
powershell.exe -NoProfile -Command "Get-PSDrive -PSProvider FileSystem | Select-Object Name,Used,Free,@{Name='FreeGiB';Expression={[math]::Round($_.Free/1GB,2)}} | Format-Table -AutoSize" >>"%HDP_LOG%" 2>&1

>>"%HDP_LOG%" echo.
>>"%HDP_LOG%" echo [Programmes disponibles]
for %%C in (winget.exe docker.exe wsl.exe git.exe code.exe powershell.exe netsh.exe netstat.exe) do where %%C >>"%HDP_LOG%" 2>&1

>>"%HDP_LOG%" echo.
>>"%HDP_LOG%" echo [Fichiers Docker connus]
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" echo Installation systeme : Docker Desktop existe.>>"%HDP_LOG%"
if exist "%ProgramFiles%\Docker\Docker\resources\bin\docker.exe" echo Installation systeme : Docker CLI existe.>>"%HDP_LOG%"
if exist "%LOCALAPPDATA%\Programs\DockerDesktop\Docker Desktop.exe" echo Installation utilisateur : Docker Desktop existe.>>"%HDP_LOG%"
if exist "%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin\docker.exe" echo Installation utilisateur : Docker CLI existe.>>"%HDP_LOG%"

>>"%HDP_LOG%" echo.
>>"%HDP_LOG%" echo [Configuration HDP non sensible]
if exist "%HDP_APP%\.env" (
  findstr.exe /B /I "HDP_PORT=" "%HDP_APP%\.env" >>"%HDP_LOG%" 2>&1
) else (
  >>"%HDP_LOG%" echo Fichier .env absent.
)

>>"%HDP_LOG%" echo.
>>"%HDP_LOG%" echo [Dernier journal de l'installateur]
if exist "%HDP_INSTALLER_LOGS%" (
  dir /o-d "%HDP_INSTALLER_LOGS%\*.log" >>"%HDP_LOG%" 2>&1
  for /f "delims=" %%L in ('dir /b /a-d /o-d "%HDP_INSTALLER_LOGS%\*.log" 2^>nul') do (
    >>"%HDP_LOG%" echo.
    >>"%HDP_LOG%" echo ----- %%L -----
    type "%HDP_INSTALLER_LOGS%\%%L" >>"%HDP_LOG%" 2>&1
    goto after_installer_log
  )
) else (
  >>"%HDP_LOG%" echo Aucun dossier de journaux trouve.
)

:after_installer_log
set "HDP_RUN_LABEL=WSL version"
set "HDP_RUN_EXE=wsl.exe"
set "HDP_RUN_ARGS=--version"
call :run_bounded

set "HDP_RUN_LABEL=WSL status"
set "HDP_RUN_EXE=wsl.exe"
set "HDP_RUN_ARGS=--status"
call :run_bounded

set "HDP_RUN_LABEL=Distributions WSL"
set "HDP_RUN_EXE=wsl.exe"
set "HDP_RUN_ARGS=--list --verbose"
call :run_bounded

set "HDP_RUN_LABEL=Docker Desktop status"
set "HDP_RUN_EXE=docker.exe"
set "HDP_RUN_ARGS=desktop status"
call :run_bounded

set "HDP_RUN_LABEL=Contextes Docker"
set "HDP_RUN_EXE=docker.exe"
set "HDP_RUN_ARGS=context ls"
call :run_bounded

set "HDP_RUN_LABEL=Docker version"
set "HDP_RUN_EXE=docker.exe"
set "HDP_RUN_ARGS=version"
call :run_bounded

set "HDP_RUN_LABEL=Docker info"
set "HDP_RUN_EXE=docker.exe"
set "HDP_RUN_ARGS=info"
call :run_bounded

set "HDP_RUN_LABEL=Ports TCP reserves par Windows"
set "HDP_RUN_EXE=netsh.exe"
set "HDP_RUN_ARGS=interface ipv4 show excludedportrange protocol=tcp"
call :run_bounded

set "HDP_RUN_LABEL=Ports TCP en ecoute"
set "HDP_RUN_EXE=netstat.exe"
set "HDP_RUN_ARGS=-ano -p tcp"
call :run_bounded

if exist "%HDP_APP%\compose.yaml" (
  set "HDP_RUN_CWD=%HDP_APP%"
  set "HDP_RUN_LABEL=Services HDP"
  set "HDP_RUN_EXE=docker.exe"
  set "HDP_RUN_ARGS=compose --profile analytics ps --all"
  call :run_bounded

  set "HDP_RUN_LABEL=Journaux des services HDP"
  set "HDP_RUN_EXE=docker.exe"
  set "HDP_RUN_ARGS=compose --profile analytics logs --no-color --tail 200"
  call :run_bounded

  >>"%HDP_LOG%" echo.
  >>"%HDP_LOG%" echo [Dossiers de donnees HDP 2.3.2]
  if exist "%HDP_APP%\data\raw" dir /s "%HDP_APP%\data\raw" >>"%HDP_LOG%" 2>&1
  if exist "%HDP_APP%\data\projects" dir /s "%HDP_APP%\data\projects" >>"%HDP_LOG%" 2>&1
) else (
  >>"%HDP_LOG%" echo.
  >>"%HDP_LOG%" echo Dossier applicatif ou compose.yaml absent : "%HDP_APP%"
)

if "%~1"=="" goto finished
if not exist "%~1" (
  call :log "Installateur introuvable : %~1"
  goto finished
)

call :log "Lancement surveille de l'installateur : %~f1"
"%~f1"
call :log "Code de sortie de l'installateur : %ERRORLEVEL%"

:finished
call :log "Diagnostic termine."
echo.
echo Journal cree :
echo "%HDP_LOG%"
echo.
echo Joignez ce fichier a votre prochaine requete GPT.
pause
exit /b 0

:run_bounded
>>"%HDP_LOG%" echo.
>>"%HDP_LOG%" echo [%HDP_RUN_LABEL% - limite 15 secondes]
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$out=[IO.Path]::GetTempFileName(); $err=[IO.Path]::GetTempFileName(); try { $p=Start-Process -FilePath $env:HDP_RUN_EXE -ArgumentList $env:HDP_RUN_ARGS -WorkingDirectory $env:HDP_RUN_CWD -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden -PassThru; if(-not $p.WaitForExit(15000)) { $p.Kill(); $p.WaitForExit(); Write-Output '[DELAI DEPASSE : processus arrete apres 15 secondes]' } else { $p.Refresh(); Write-Output ('[code de sortie : ' + $p.ExitCode + ']') }; $encoding=if($env:HDP_RUN_EXE -ieq 'wsl.exe') {[Text.Encoding]::Unicode} else {[Text.Encoding]::Default}; if((Test-Path $out) -and ((Get-Item $out).Length -gt 0)) { [IO.File]::ReadAllText($out,$encoding) }; if((Test-Path $err) -and ((Get-Item $err).Length -gt 0)) { [IO.File]::ReadAllText($err,$encoding) } } catch { Write-Output ('[ERREUR : ' + $_.Exception.Message + ']') } finally { Remove-Item -LiteralPath $out,$err -Force -ErrorAction SilentlyContinue }" >>"%HDP_LOG%" 2>&1
exit /b 0

:log
>>"%HDP_LOG%" echo %~1
exit /b 0
