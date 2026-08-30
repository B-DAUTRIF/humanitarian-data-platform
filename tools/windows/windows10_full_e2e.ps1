[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$InstallerPath
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$os=Get-CimInstance Win32_OperatingSystem
$build=[int]$os.BuildNumber
$arch=$os.OSArchitecture
# Windows 10 21H2/22H2 and LTSC 2021 are the supported V6 baseline.
if($os.Caption -notmatch 'Windows 10'){ throw "Recette Windows 10 exécutée sur un autre OS: $($os.Caption)" }
if($arch -notmatch '64'){ throw "Windows 10 x64 requis, architecture détectée: $arch" }
if($build -lt 19044 -or $build -ge 22000){ throw "Build Windows 10 non qualifié: $build (minimum V6: 19044)." }
Write-Host "WINDOWS10_OS_CONFIRMED=$($os.Caption);build=$build;arch=$arch"
& (Join-Path $PSScriptRoot 'windows10_compatibility_gate.ps1') -InstallerPath $InstallerPath
if($LASTEXITCODE -ne 0){ throw 'Gate statique Windows 10 en échec.' }
& (Join-Path $PSScriptRoot 'windows_installer_e2e.ps1') -InstallerPath $InstallerPath
if($LASTEXITCODE -ne 0){ throw 'Parcours installateur Windows 10 en échec.' }
Write-Host 'WINDOWS10_FULL_E2E=PASS'
