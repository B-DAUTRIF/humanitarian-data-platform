param(
  [Parameter(Mandatory=$true)][string]$Archive,
  [string]$ApplicationDirectory = $PSScriptRoot,
  [Parameter(Mandatory=$true)][ValidateSet("RESTORE-HDP")][string]$Confirmation
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path $Archive)) { throw "Archive de sauvegarde introuvable" }
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$stage = Join-Path ([System.IO.Path]::GetTempPath()) "HDP_restore_$stamp"
Expand-Archive -Path $Archive -DestinationPath $stage
if (-not (Test-Path (Join-Path $stage "MANIFEST.txt"))) { throw "Manifeste HDP absent" }
if (-not (Select-String -Path (Join-Path $stage "MANIFEST.txt") -Pattern "HDP_BACKUP_VERSION=4.0.0" -Quiet)) { throw "Version de sauvegarde incompatible" }
Push-Location $ApplicationDirectory
try {
  & (Join-Path $ApplicationDirectory "backup-hdp.ps1") -ApplicationDirectory $ApplicationDirectory
  docker compose down
  if (Test-Path ".env") { Move-Item ".env" ".env.before-restore-$stamp" }
  Copy-Item (Join-Path $stage ".env") ".env"
  if (Test-Path "data") { Move-Item "data" "data.before-restore-$stamp" }
  if (Test-Path (Join-Path $stage "data")) { Copy-Item (Join-Path $stage "data") "data" -Recurse } else { New-Item -ItemType Directory "data" | Out-Null }
  docker compose up -d db
  $ready = $false
  for ($attempt = 0; $attempt -lt 60; $attempt++) {
    docker compose exec -T db pg_isready -U humanitarian -d humanitarian *> $null
    if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    Start-Sleep -Seconds 2
  }
  if (-not $ready) { throw "PostgreSQL n’est pas prêt" }
  docker compose cp (Join-Path $stage "database.dump") db:/tmp/hdp-restore.dump
  docker compose exec -T db pg_restore -U humanitarian -d humanitarian --clean --if-exists --no-owner /tmp/hdp-restore.dump
  docker compose exec -T db rm -f /tmp/hdp-restore.dump
  docker compose up -d
  Write-Host "Restauration terminée. Les anciens .env et data ont été conservés avec le suffixe $stamp."
} finally {
  Pop-Location
  Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
}
