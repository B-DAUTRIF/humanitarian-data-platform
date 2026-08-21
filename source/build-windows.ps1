[CmdletBinding()]
param(
    [string]$OutputDirectory = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$sourceDirectory = Split-Path -Parent $PSCommandPath
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $sourceDirectory "windows-build"
}
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
$installerName = "HumanitarianDataPlatform_Setup_Native_GUI_v6.0.0-dev.exe"
$installerPath = Join-Path $OutputDirectory $installerName

$vswhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path -LiteralPath $vswhere -PathType Leaf)) {
    throw "vswhere.exe introuvable : Visual Studio Build Tools est requis."
}

$visualStudio = & $vswhere -latest -products * `
    -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
    -property installationPath
if ([string]::IsNullOrWhiteSpace($visualStudio)) {
    throw "Aucun environnement MSVC x64 compatible n'a été trouvé."
}
$vcvars = Join-Path $visualStudio "VC\Auxiliary\Build\vcvars64.bat"
if (-not (Test-Path -LiteralPath $vcvars -PathType Leaf)) {
    throw "vcvars64.bat introuvable dans $visualStudio."
}

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
Push-Location $sourceDirectory
try {
    & node "scripts/generate_payload.mjs" "payload" "src/payload_generated.h"
    if ($LASTEXITCODE -ne 0) {
        throw "La génération du payload a échoué ($LASTEXITCODE)."
    }

    # A temporary batch file avoids cmd.exe /S /C quote stripping, which can
    # otherwise pass the compiler commands themselves to vcvars64.bat.
    $buildScript = Join-Path $OutputDirectory "build-msvc.cmd"
    $compilerCommand = 'cl.exe /nologo /O2 /W4 /WX /utf-8 /std:c17 /D_CRT_SECURE_NO_WARNINGS "src\installer.c" "src\installer.res" ' +
        "/link /OUT:`"$installerPath`" /SUBSYSTEM:WINDOWS /MACHINE:X64 " +
        '/DYNAMICBASE /NXCOMPAT /HIGHENTROPYVA comctl32.lib shell32.lib ' +
        'advapi32.lib winhttp.lib ws2_32.lib bcrypt.lib gdi32.lib user32.lib ole32.lib uuid.lib || exit /b 1'
    $commands = @(
        '@echo off'
        ('call "{0}" || exit /b 1' -f $vcvars)
        'rc.exe /nologo /c 65001 /fo "src\installer.res" "src\installer.rc" || exit /b 1'
        $compilerCommand
    )
    Set-Content -LiteralPath $buildScript -Encoding ascii -Value $commands

    & $buildScript
    if ($LASTEXITCODE -ne 0) {
        throw "La compilation MSVC a échoué ($LASTEXITCODE)."
    }
}
finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) {
    throw "L'installateur attendu n'a pas été produit : $installerPath"
}

$version = (Get-Item -LiteralPath $installerPath).VersionInfo
if ($version.FileVersion -notlike "6.0.0*" -or $version.ProductVersion -notlike "6.0.0-dev*") {
    throw "Métadonnées inattendues : FileVersion=$($version.FileVersion), ProductVersion=$($version.ProductVersion)"
}

$toolsDirectory = Join-Path $visualStudio "VC\Tools\MSVC"
$dumpbinExecutable = Get-ChildItem -LiteralPath $toolsDirectory -Filter dumpbin.exe -Recurse |
    Where-Object { $_.FullName -match 'Hostx64\\x64\\dumpbin\.exe$' } |
    Select-Object -First 1
if (-not $dumpbinExecutable) {
    throw "dumpbin.exe x64 introuvable."
}
$headers = & $dumpbinExecutable.FullName /headers $installerPath | Out-String
if ($LASTEXITCODE -ne 0 -or $headers -notmatch "machine \(x64\)" -or $headers -notmatch "Windows GUI") {
    throw "Le contrôle PE32+ GUI x64 a échoué."
}

$hash = (Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash.ToLowerInvariant()
$hashFile = "$installerPath.sha256"
Set-Content -LiteralPath $hashFile -Encoding ascii -NoNewline `
    -Value "$hash  $installerName`n"

Write-Host "Installateur Windows vérifié : $installerPath"
Write-Host "SHA-256 : $hash"
