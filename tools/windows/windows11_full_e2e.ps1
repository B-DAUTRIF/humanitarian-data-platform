[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$InstallerPath
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$os=Get-CimInstance Win32_OperatingSystem
$build=[int]$os.BuildNumber
$arch=$os.OSArchitecture
if($os.Caption -notmatch 'Windows 11'){ throw "Recette Windows 11 exécutée sur un autre OS: $($os.Caption)" }
if($arch -notmatch '64'){ throw "Windows 11 x64 requis, architecture détectée: $arch" }
if($build -lt 22000){ throw "Build Windows 11 non qualifié: $build." }
Write-Host "WINDOWS11_OS_CONFIRMED=$($os.Caption);build=$build;arch=$arch"
& (Join-Path $PSScriptRoot 'windows10_compatibility_gate.ps1') -InstallerPath $InstallerPath
if($LASTEXITCODE -ne 0){ throw 'Gate binaire/API Windows 10+ en échec.' }
& (Join-Path $PSScriptRoot 'windows_installer_e2e.ps1') -InstallerPath $InstallerPath
if($LASTEXITCODE -ne 0){ throw 'Parcours installateur Windows 11 en échec.' }
Write-Host 'WINDOWS11_FULL_E2E=PASS'
