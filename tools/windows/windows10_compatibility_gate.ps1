[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$InstallerPath,
    [string]$DumpbinPath = ""
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$build = Get-Content (Join-Path $root 'source\build-windows.ps1') -Raw
$installerSource = Get-Content (Join-Path $root 'source\src\installer.c') -Raw
if($build -notmatch '_WIN32_WINNT=0x0A00'){ throw 'La compilation ne cible pas explicitement Windows 10 (_WIN32_WINNT=0x0A00).' }
if($build -notmatch 'NTDDI_VERSION=0x0A000000'){ throw 'La compilation ne cible pas explicitement NTDDI Windows 10.' }
# Interdire le contournement silencieux du ciblage SDK par chargement dynamique d'API.
if($installerSource -match '\bGetProcAddress\s*\(' -or $installerSource -match '\bLoadLibrary(?:Ex)?[AW]?\s*\('){
    throw 'Chargement dynamique d API Win32 détecté : toute API optionnelle doit avoir un fallback Windows 10 explicitement testé.'
}
if(!(Test-Path -LiteralPath $InstallerPath -PathType Leaf)){ throw "Installateur absent: $InstallerPath" }
$vi=(Get-Item -LiteralPath $InstallerPath).VersionInfo
if($vi.FileVersion -notlike '6.0.0*' -or $vi.ProductVersion -notlike '6.0.0*'){ throw 'Version installateur incorrecte.' }
if([string]::IsNullOrWhiteSpace($DumpbinPath)){
    $vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    $vs=& $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    $DumpbinPath=(Get-ChildItem "$vs\VC\Tools\MSVC" -Filter dumpbin.exe -Recurse | Where-Object FullName -match 'Hostx64\\x64\\dumpbin\.exe$' | Select-Object -First 1).FullName
}
$headers=& $DumpbinPath /headers $InstallerPath | Out-String
$imports=& $DumpbinPath /imports $InstallerPath | Out-String
if($headers -notmatch 'machine \(x64\)' -or $headers -notmatch 'Windows GUI'){ throw 'PE x64 GUI attendu.' }
$forbidden=@('WindowsAppRuntime','Microsoft\.UI\.Xaml','api-ms-win-core-windowserrorreporting-l1-1-3')
foreach($pattern in $forbidden){ if($imports -match $pattern){ throw "Dépendance post-Windows-10 interdite détectée: $pattern" } }
Write-Host 'WINDOWS10_STATIC_COMPATIBILITY=PASS'
Write-Host 'TARGET=_WIN32_WINNT=0x0A00;NTDDI_VERSION=0x0A000000;x64'
