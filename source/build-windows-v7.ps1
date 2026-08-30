[CmdletBinding()]
param(
    [string]$OutputDirectory = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$sourceDirectory = Split-Path -Parent $PSCommandPath
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $sourceDirectory "windows-build-v7"
}
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
$installerName = "HumanitarianDataPlatform_Setup_Native_GUI_v7.0.0.exe"
$installerPath = Join-Path $OutputDirectory $installerName

$vswhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path -LiteralPath $vswhere -PathType Leaf)) { throw "vswhere.exe introuvable : Visual Studio Build Tools est requis." }
$visualStudio = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if ([string]::IsNullOrWhiteSpace($visualStudio)) { throw "Aucun environnement MSVC x64 compatible n'a été trouvé." }
$vcvars = Join-Path $visualStudio "VC\Auxiliary\Build\vcvars64.bat"
if (-not (Test-Path -LiteralPath $vcvars -PathType Leaf)) { throw "vcvars64.bat introuvable dans $visualStudio." }

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$work = Join-Path $env:RUNNER_TEMP "hdp-v7-installer-source"
if (Test-Path $work) { Remove-Item -Recurse -Force $work }
New-Item -ItemType Directory -Force -Path $work | Out-Null
Copy-Item -Recurse (Join-Path $sourceDirectory "src") (Join-Path $work "src")

# Derive V7 metadata in an isolated tree so the previously qualified V6 installer
# source remains available for backward-compatibility qualification.
$cPath = Join-Path $work "src\installer.c"
$rcPath = Join-Path $work "src\installer.rc"
$manifestPath = Join-Path $work "src\installer.manifest"
$c = Get-Content -Raw -LiteralPath $cPath
$c = $c -replace '#define APP_VERSION L"[^"]+"', '#define APP_VERSION L"7.0.0"'
Set-Content -LiteralPath $cPath -Encoding utf8 -NoNewline -Value $c
$rc = Get-Content -Raw -LiteralPath $rcPath
$rc = $rc -replace 'FILEVERSION\s+\d+,\d+,\d+,\d+', 'FILEVERSION 7,0,0,0'
$rc = $rc -replace 'PRODUCTVERSION\s+\d+,\d+,\d+,\d+', 'PRODUCTVERSION 7,0,0,0'
$rc = $rc -replace 'VALUE "FileVersion", "[^"]+"', 'VALUE "FileVersion", "7.0.0.0"'
$rc = $rc -replace 'VALUE "ProductVersion", "[^"]+"', 'VALUE "ProductVersion", "7.0.0"'
$rc = $rc -replace 'VALUE "OriginalFilename", "[^"]+"', 'VALUE "OriginalFilename", "HumanitarianDataPlatform_Setup_Native_GUI_v7.0.0.exe"'
Set-Content -LiteralPath $rcPath -Encoding utf8 -NoNewline -Value $rc
$manifest = Get-Content -Raw -LiteralPath $manifestPath
$manifest = $manifest -replace '(<assemblyIdentity version=")[^"]+(" processorArchitecture="amd64" name="HDP.NativeInstaller")', '${1}7.0.0.0${2}'
Set-Content -LiteralPath $manifestPath -Encoding utf8 -NoNewline -Value $manifest

Push-Location $sourceDirectory
try {
    & node "scripts/generate_payload.mjs" "payload" (Join-Path $work "src\payload_generated.h")
    if ($LASTEXITCODE -ne 0) { throw "La génération du payload V7 a échoué ($LASTEXITCODE)." }
}
finally { Pop-Location }

$buildScript = Join-Path $OutputDirectory "build-msvc-v7.cmd"
$installerC = Join-Path $work "src\installer.c"
$installerRc = Join-Path $work "src\installer.rc"
$installerRes = Join-Path $work "src\installer.res"
$compilerCommand = 'cl.exe /nologo /O2 /W4 /WX /utf-8 /std:c17 /D_CRT_SECURE_NO_WARNINGS /D_WIN32_WINNT=0x0A00 /DNTDDI_VERSION=0x0A000000 ' +
    ('"{0}" "{1}" ' -f $installerC, $installerRes) +
    ('/link /OUT:"{0}" /SUBSYSTEM:WINDOWS /MACHINE:X64 /DYNAMICBASE /NXCOMPAT /HIGHENTROPYVA comctl32.lib shell32.lib advapi32.lib winhttp.lib ws2_32.lib bcrypt.lib gdi32.lib user32.lib ole32.lib uuid.lib || exit /b 1' -f $installerPath)
$commands = @(
    '@echo off',
    ('call "{0}" || exit /b 1' -f $vcvars),
    ('rc.exe /nologo /c 65001 /fo "{0}" "{1}" || exit /b 1' -f $installerRes, $installerRc),
    $compilerCommand
)
Set-Content -LiteralPath $buildScript -Encoding ascii -Value $commands
& $buildScript
if ($LASTEXITCODE -ne 0) { throw "La compilation MSVC V7 a échoué ($LASTEXITCODE)." }

if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) { throw "Installateur V7 absent : $installerPath" }
$version = (Get-Item -LiteralPath $installerPath).VersionInfo
if ($version.FileVersion -notlike "7.0.0*" -or $version.ProductVersion -notlike "7.0.0*") { throw "Métadonnées V7 inattendues : FileVersion=$($version.FileVersion), ProductVersion=$($version.ProductVersion)" }
$hash = (Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content -LiteralPath "$installerPath.sha256" -Encoding ascii -NoNewline -Value "$hash  $installerName`n"
Write-Host "Installateur HDP V7 Windows 10/11 x64 : $installerPath"
Write-Host "SHA-256 : $hash"
