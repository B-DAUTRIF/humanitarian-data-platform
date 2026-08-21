param(
  [string]$ApplicationDirectory = $PSScriptRoot,
  [string]$OutputDirectory = (Join-Path $PSScriptRoot "backups")
)
$ErrorActionPreference = "Stop"
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$stage = Join-Path $OutputDirectory "HDP_backup_$stamp"
$archive = "$stage.zip"
$compose = Join-Path $ApplicationDirectory "compose.yaml"
$envFile = Join-Path $ApplicationDirectory ".env"
New-Item -ItemType Directory -Force -Path $stage | Out-Null
if (-not (Test-Path -LiteralPath $compose -PathType Leaf)) { throw "compose.yaml introuvable" }
if (-not (Test-Path -LiteralPath $envFile -PathType Leaf)) { throw ".env introuvable" }

function Invoke-HdpCompose([string[]]$Arguments) {
  & docker compose --project-directory $ApplicationDirectory -f $compose --env-file $envFile @Arguments
  if ($LASTEXITCODE -ne 0) { throw "Échec de docker compose: $($Arguments -join ' ')" }
}

Push-Location $ApplicationDirectory
try {
  Invoke-HdpCompose @("exec", "-T", "db", "pg_dump", "-U", "humanitarian", "-d", "humanitarian", "-Fc", "-f", "/tmp/hdp-backup.dump")
  Invoke-HdpCompose @("cp", "db:/tmp/hdp-backup.dump", (Join-Path $stage "database.dump"))
  Invoke-HdpCompose @("exec", "-T", "db", "rm", "-f", "/tmp/hdp-backup.dump")
  if (Test-Path -LiteralPath "data" -PathType Container) {
    Copy-Item -LiteralPath "data" -Destination (Join-Path $stage "data") -Recurse
  }
  @(
    "HDP_BACKUP_VERSION=6.0.0-dev",
    "CREATED_AT_UTC=$((Get-Date).ToUniversalTime().ToString('o'))",
    "SECRETS_INCLUDED=false",
    "CONFIGURATION_POLICY=Conserver le .env de l'installation cible"
  ) | Set-Content (Join-Path $stage "MANIFEST.txt") -Encoding UTF8

  $files = Get-ChildItem -LiteralPath $stage -File -Recurse | Sort-Object FullName
  $files | ForEach-Object {
    $relative = [IO.Path]::GetRelativePath($stage, $_.FullName).Replace('\', '/')
    "{0}  {1}" -f (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant(), $relative
  } | Set-Content (Join-Path $stage "SHA256SUMS.txt") -Encoding ASCII

  Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $archive -CompressionLevel Optimal
  $archiveHash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
  "$archiveHash  $([IO.Path]::GetFileName($archive))" | Set-Content "$archive.sha256" -Encoding ASCII
  Write-Host "Sauvegarde créée: $archive"
  Write-Host "Somme externe: $archive.sha256"
  Write-Host "SHA-256: $archiveHash"
} finally {
  Pop-Location
  Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
}
