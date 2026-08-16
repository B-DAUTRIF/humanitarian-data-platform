param(
  [Parameter(Mandatory=$true)][string]$Archive,
  [string]$ExpectedSha256 = "",
  [string]$ApplicationDirectory = $PSScriptRoot,
  [Parameter(Mandatory=$true)][ValidateSet("RESTORE-HDP")][string]$Confirmation
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression.FileSystem

$archivePath = (Resolve-Path -LiteralPath $Archive).Path
$compose = Join-Path $ApplicationDirectory "compose.yaml"
$envFile = Join-Path $ApplicationDirectory ".env"
if (-not (Test-Path -LiteralPath $compose -PathType Leaf)) { throw "compose.yaml de confiance introuvable" }
if (-not (Test-Path -LiteralPath $envFile -PathType Leaf)) { throw ".env actif introuvable" }

if (-not $ExpectedSha256) {
  $sidecar = "$archivePath.sha256"
  if (-not (Test-Path -LiteralPath $sidecar -PathType Leaf)) {
    throw "Somme externe absente. Fournissez -ExpectedSha256 ou le fichier .sha256 associé."
  }
  $ExpectedSha256 = ((Get-Content -LiteralPath $sidecar -Raw).Trim() -split '\s+')[0]
}
if ($ExpectedSha256 -notmatch '^[0-9a-fA-F]{64}$') { throw "SHA-256 externe invalide" }
$actualArchiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
if ($actualArchiveHash -ne $ExpectedSha256) { throw "L'archive ne correspond pas à la somme SHA-256 externe" }

$zip = [IO.Compression.ZipFile]::OpenRead($archivePath)
try {
  if ($zip.Entries.Count -gt 20000) { throw "Archive trop volumineuse en nombre d'entrées" }
  [Int64]$expanded = 0
  foreach ($entry in $zip.Entries) {
    $name = $entry.FullName.Replace('\', '/')
    if (-not $name -or $name.StartsWith('/') -or $name -match '(^|/)\.\.(/|$)' -or $name -match '^[A-Za-z]:') {
      throw "Chemin d'archive interdit: $name"
    }
    if ($name -notin @('MANIFEST.txt', 'SHA256SUMS.txt', 'database.dump') -and -not $name.StartsWith('data/')) {
      throw "Entrée non autorisée dans la sauvegarde: $name"
    }
    $unixMode = (($entry.ExternalAttributes -shr 16) -band 0xF000)
    if ($unixMode -eq 0xA000) { throw "Lien symbolique interdit dans la sauvegarde: $name" }
    $expanded += $entry.Length
    if ($entry.Length -gt 2147483648) { throw "Entrée supérieure à 2 Gio: $name" }
    if ($entry.CompressedLength -gt 0 -and ($entry.Length / $entry.CompressedLength) -gt 500) {
      throw "Ratio de compression suspect: $name"
    }
  }
  if ($expanded -gt 10737418240) { throw "Archive supérieure à 10 Gio après décompression" }
} finally {
  $zip.Dispose()
}

$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$stage = Join-Path ([IO.Path]::GetTempPath()) "HDP_restore_$stamp-$([Guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $stage | Out-Null
[IO.Compression.ZipFile]::ExtractToDirectory($archivePath, $stage)

function Invoke-HdpCompose([string[]]$Arguments) {
  & docker compose --project-directory $ApplicationDirectory -f $compose --env-file $envFile @Arguments
  if ($LASTEXITCODE -ne 0) { throw "Échec de docker compose: $($Arguments -join ' ')" }
}

try {
  $manifest = Join-Path $stage "MANIFEST.txt"
  $sums = Join-Path $stage "SHA256SUMS.txt"
  if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) { throw "Manifeste HDP absent" }
  if (-not (Select-String -LiteralPath $manifest -Pattern '^HDP_BACKUP_VERSION=5\.0\.0$' -Quiet)) {
    throw "Version de sauvegarde incompatible"
  }
  if (-not (Test-Path -LiteralPath $sums -PathType Leaf)) { throw "SHA256SUMS.txt absent" }

  $expectedFiles = @{}
  foreach ($line in Get-Content -LiteralPath $sums) {
    if ($line -notmatch '^([0-9a-f]{64})  ([^\r\n]+)$') { throw "Ligne SHA256SUMS invalide" }
    $relative = $Matches[2].Replace('\', '/')
    if ($expectedFiles.ContainsKey($relative)) { throw "Entrée SHA-256 dupliquée: $relative" }
    $expectedFiles[$relative] = $Matches[1]
  }
  $actualFiles = Get-ChildItem -LiteralPath $stage -File -Recurse |
    Where-Object { $_.FullName -ne $sums }
  foreach ($file in $actualFiles) {
    $relative = [IO.Path]::GetRelativePath($stage, $file.FullName).Replace('\', '/')
    if (-not $expectedFiles.ContainsKey($relative)) { throw "Fichier non manifesté: $relative" }
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $expectedFiles[$relative]) { throw "Empreinte incorrecte: $relative" }
    $expectedFiles.Remove($relative)
  }
  if ($expectedFiles.Count -ne 0) { throw "Le manifeste référence des fichiers absents" }

  Get-ChildItem Env: | Where-Object { $_.Name -like 'COMPOSE_*' -or $_.Name -like 'DOCKER_*' } |
    ForEach-Object { Remove-Item "Env:$($_.Name)" }

  & (Join-Path $ApplicationDirectory "backup-hdp.ps1") -ApplicationDirectory $ApplicationDirectory
  if ($LASTEXITCODE -ne 0) { throw "La sauvegarde de sécurité préalable a échoué" }
  Invoke-HdpCompose @("down")
  if (Test-Path -LiteralPath (Join-Path $ApplicationDirectory "data")) {
    Move-Item -LiteralPath (Join-Path $ApplicationDirectory "data") -Destination (Join-Path $ApplicationDirectory "data.before-restore-$stamp")
  }
  if (Test-Path -LiteralPath (Join-Path $stage "data")) {
    Copy-Item -LiteralPath (Join-Path $stage "data") -Destination (Join-Path $ApplicationDirectory "data") -Recurse
  } else {
    New-Item -ItemType Directory -Path (Join-Path $ApplicationDirectory "data") | Out-Null
  }
  Invoke-HdpCompose @("up", "-d", "db")
  $ready = $false
  for ($attempt = 0; $attempt -lt 60; $attempt++) {
    & docker compose --project-directory $ApplicationDirectory -f $compose --env-file $envFile exec -T db pg_isready -U humanitarian -d humanitarian *> $null
    if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    Start-Sleep -Seconds 2
  }
  if (-not $ready) { throw "PostgreSQL n'est pas prêt" }
  Invoke-HdpCompose @("cp", (Join-Path $stage "database.dump"), "db:/tmp/hdp-restore.dump")
  Invoke-HdpCompose @("exec", "-T", "db", "pg_restore", "-U", "humanitarian", "-d", "humanitarian", "--clean", "--if-exists", "--no-owner", "/tmp/hdp-restore.dump")
  Invoke-HdpCompose @("exec", "-T", "db", "rm", "-f", "/tmp/hdp-restore.dump")
  Invoke-HdpCompose @("up", "-d")
  Write-Host "Restauration V5 terminée. Le .env actif et ses secrets ont été conservés."
} finally {
  Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
}
