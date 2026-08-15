param(
  [string]$ApplicationDirectory = $PSScriptRoot,
  [string]$OutputDirectory = (Join-Path $PSScriptRoot "backups")
)
$ErrorActionPreference = "Stop"
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$stage = Join-Path $OutputDirectory "HDP_backup_$stamp"
$archive = "$stage.zip"
New-Item -ItemType Directory -Force -Path $stage | Out-Null
if (-not (Test-Path (Join-Path $ApplicationDirectory "compose.yaml"))) { throw "compose.yaml introuvable" }
if (-not (Test-Path (Join-Path $ApplicationDirectory ".env"))) { throw ".env introuvable" }
Push-Location $ApplicationDirectory
try {
  docker compose exec -T db pg_dump -U humanitarian -d humanitarian -Fc -f /tmp/hdp-backup.dump
  docker compose cp db:/tmp/hdp-backup.dump (Join-Path $stage "database.dump")
  docker compose exec -T db rm -f /tmp/hdp-backup.dump
  Copy-Item ".env" (Join-Path $stage ".env")
  if (Test-Path "data") { Copy-Item "data" (Join-Path $stage "data") -Recurse }
  @(
    "HDP_BACKUP_VERSION=4.0.0",
    "CREATED_AT_UTC=$((Get-Date).ToUniversalTime().ToString('o'))",
    "WARNING=Cette archive contient les secrets de .env; conservez-la hors du depot."
  ) | Set-Content (Join-Path $stage "MANIFEST.txt") -Encoding UTF8
  Get-ChildItem $stage -File -Recurse | ForEach-Object {
    "{0}  {1}" -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant(), $_.FullName.Substring($stage.Length + 1)
  } | Set-Content (Join-Path $stage "SHA256SUMS.txt") -Encoding ASCII
  Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $archive -CompressionLevel Optimal
  Write-Host "Sauvegarde créée: $archive"
  Write-Host "SHA-256: $((Get-FileHash $archive -Algorithm SHA256).Hash.ToLowerInvariant())"
} finally {
  Pop-Location
}

