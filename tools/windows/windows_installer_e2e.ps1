param(
    [Parameter(Mandatory = $true)]
    [string]$InstallerPath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if (-not (Test-Path -LiteralPath $InstallerPath)) { throw "Installateur introuvable: $InstallerPath" }
$installerResolved = (Resolve-Path $InstallerPath).Path
$installerDir = Split-Path -Parent $installerResolved
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$work = Join-Path $env:RUNNER_TEMP 'hdp-installer-e2e'
$fakeBin = Join-Path $work 'fake-bin'
$installDir = Join-Path $work 'installed-HDP'
New-Item -ItemType Directory -Force -Path $fakeBin,$installDir | Out-Null

$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
if (-not (Test-Path -LiteralPath $vswhere)) { throw 'vswhere.exe introuvable' }
$vs = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $vs) { throw 'MSVC x64 introuvable' }
$devCmd = Join-Path $vs 'Common7\Tools\VsDevCmd.bat'
$fakeSource = Join-Path $root 'tools\windows\fake_docker.c'
$fakeDocker = Join-Path $fakeBin 'docker.exe'
$installerLocalDocker = Join-Path $installerDir 'docker.exe'
$compile = "call `"$devCmd`" -no_logo -arch=x64 && cl /nologo /O2 /W4 /WX /Fe:`"$fakeDocker`" `"$fakeSource`" ws2_32.lib"
& cmd.exe /d /s /c $compile
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $fakeDocker)) { throw "Compilation du Docker contrôlé échouée ($LASTEXITCODE)" }
Copy-Item -LiteralPath $fakeDocker -Destination $installerLocalDocker -Force
$env:PATH = "$fakeBin;$env:PATH"

Add-Type @'
using System;
using System.Text;
using System.Runtime.InteropServices;
public static class HDPWin32 {
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr GetDlgItem(IntPtr hWnd, int nIDDlgItem);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern bool SetWindowText(IntPtr hWnd, string lpString);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
    [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
}
'@

$BM_CLICK=0x00F5; $BM_SETCHECK=0x00F1; $BST_UNCHECKED=0; $BST_CHECKED=1; $IDYES=6; $IDOK=1

function Wait-MainWindow([System.Diagnostics.Process]$Process,[int]$TimeoutSeconds=30) {
    $deadline=(Get-Date).AddSeconds($TimeoutSeconds)
    do {
        Start-Sleep -Milliseconds 250; $Process.Refresh()
        if($Process.HasExited){throw "L'installateur s'est arrêté prématurément: $($Process.ExitCode)"}
        if($Process.MainWindowHandle -ne [IntPtr]::Zero){return $Process.MainWindowHandle}
    } while((Get-Date)-lt $deadline)
    throw 'Fenêtre principale de l installateur introuvable'
}
function Get-Control([IntPtr]$Window,[int]$Id) {
    $control=[HDPWin32]::GetDlgItem($Window,$Id)
    if($control -eq [IntPtr]::Zero){throw "Contrôle Windows ID=$Id introuvable"}; return $control
}
function Wait-Control([IntPtr]$Window,[int]$Id,[int]$TimeoutSeconds=10) {
    $deadline=(Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $control=[HDPWin32]::GetDlgItem($Window,$Id)
        if($control -ne [IntPtr]::Zero){return $control}
        Start-Sleep -Milliseconds 100
    } while((Get-Date)-lt $deadline)
    throw "Contrôle ID=$Id absent dans le délai attendu"
}
function Set-ControlText([IntPtr]$Window,[int]$Id,[string]$Value) { $control=Get-Control $Window $Id; if(-not [HDPWin32]::SetWindowText($control,$Value)){throw "SetWindowText ID=$Id a échoué"} }
function Set-Check([IntPtr]$Window,[int]$Id,[bool]$Checked) { $control=Get-Control $Window $Id; $value=if($Checked){$BST_CHECKED}else{$BST_UNCHECKED}; [void][HDPWin32]::SendMessage($control,$BM_SETCHECK,[IntPtr]$value,[IntPtr]::Zero) }
function Click-Control([IntPtr]$Window,[int]$Id) { $control=Get-Control $Window $Id; if(-not [HDPWin32]::PostMessage($control,$BM_CLICK,[IntPtr]::Zero,[IntPtr]::Zero)){throw "PostMessage BM_CLICK ID=$Id a échoué"} }
function Get-ControlText([IntPtr]$Window,[int]$Id) { $control=Get-Control $Window $Id; $buffer=New-Object System.Text.StringBuilder 2048; [void][HDPWin32]::GetWindowText($control,$buffer,$buffer.Capacity); return $buffer.ToString() }
function Click-DialogButton([int]$Id,[int]$TimeoutSeconds=20) {
    $deadline=(Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $dialog=[HDPWin32]::FindWindow('#32770','Humanitarian Data Platform')
        if($dialog -ne [IntPtr]::Zero){$button=[HDPWin32]::GetDlgItem($dialog,$Id); if($button -ne [IntPtr]::Zero){if(-not [HDPWin32]::PostMessage($button,$BM_CLICK,[IntPtr]::Zero,[IntPtr]::Zero)){throw "PostMessage dialogue ID=$Id a échoué"}; Start-Sleep -Milliseconds 250; return}}
        Start-Sleep -Milliseconds 200
    } while((Get-Date)-lt $deadline)
    throw "Dialogue HDP avec bouton ID=$Id introuvable"
}
function Wait-Status([IntPtr]$Window,[string]$Needle,[int]$TimeoutSeconds=180) {
    $deadline=(Get-Date).AddSeconds($TimeoutSeconds); $last=''
    do {$last=Get-ControlText $Window 1011; if($last -like "*$Needle*"){return $last}; if($last -like '*interrompue*' -or $last -like '*annulée*'){throw "Statut d'échec détecté: $last"}; Start-Sleep -Milliseconds 500} while((Get-Date)-lt $deadline)
    throw "Délai dépassé en attente du statut '$Needle'. Dernier statut: $last"
}
function Assert-File([string]$Path) { if(-not(Test-Path -LiteralPath $Path -PathType Leaf)){throw "Fichier attendu absent: $Path"} }

$desktop=[Environment]::GetFolderPath('Desktop'); $shortcut=Join-Path $desktop 'Humanitarian Data Platform.lnk'; $process=$null
try {
    $process=Start-Process -FilePath $installerResolved -PassThru
    $window=Wait-MainWindow $process
    [void](Wait-Control $window 1001)
    Start-Sleep -Milliseconds 750
    Set-ControlText $window 1001 $installDir
    Set-ControlText $window 1002 'hdp-ci-qualification'
    Set-ControlText $window 1014 ''
    Set-Check $window 1013 $true
    Start-Sleep -Milliseconds 250
    if((Get-ControlText $window 1001)-ne $installDir){throw 'Le chemin de recette n a pas été appliqué à la GUI'}
    if((Get-ControlText $window 1002)-ne 'hdp-ci-qualification'){throw 'L appname ReliefWeb de recette n a pas été appliqué'}
    Click-Control $window 1007; Click-DialogButton $IDYES; [void](Wait-Status $window 'Installation terminée'); Click-DialogButton $IDOK

    Assert-File (Join-Path $installDir 'compose.yaml'); Assert-File (Join-Path $installDir 'start-hdp.cmd'); Assert-File (Join-Path $installDir 'start-hdp-with-r.cmd'); Assert-File (Join-Path $installDir '.env'); Assert-File (Join-Path $installDir '.hdp-managed-installation'); Assert-File $shortcut
    $envPath=Join-Path $installDir '.env'; $envText=Get-Content -Raw -LiteralPath $envPath
    if($envText -notmatch '(?m)^HDP_AUTH_MODE=passkey\s*$'){throw 'HDP_AUTH_MODE=passkey absent de .env'}
    if($envText -notmatch '(?m)^HDP_PORT=\d+\s*$'){throw 'HDP_PORT absent de .env'}
    Add-Content -LiteralPath $envPath -Value 'CUSTOM_QUALIFICATION_VALUE=preserve-me'

    Click-Control $window 1007; Click-DialogButton $IDYES; [void](Wait-Status $window 'Installation terminée'); Click-DialogButton $IDOK
    $backup=Join-Path $installDir '.env.backup-before-v6.0.0'; Assert-File $backup
    $current=Get-Content -Raw -LiteralPath $envPath; $previous=Get-Content -Raw -LiteralPath $backup
    if($current -notmatch 'CUSTOM_QUALIFICATION_VALUE=preserve-me'){throw 'La mise à niveau a perdu une variable utilisateur'}
    if($previous -notmatch 'CUSTOM_QUALIFICATION_VALUE=preserve-me'){throw 'La sauvegarde .env ne contient pas la valeur utilisateur'}
    Assert-File $shortcut

    Click-Control $window 1016; Click-DialogButton $IDYES; [void](Wait-Status $window 'Désinstallation terminée'); Click-DialogButton $IDOK
    Assert-File $envPath; Assert-File $backup
    if(Test-Path -LiteralPath $shortcut){throw 'Le raccourci HDP est resté après désinstallation contrôlée'}
    if(Test-Path -LiteralPath (Join-Path $installDir '.hdp-managed-installation')){throw 'Le marqueur géré est resté après désinstallation'}
    if(Test-Path -LiteralPath (Join-Path $installDir 'compose.yaml')){throw 'Le payload géré est resté après désinstallation'}
    $after=Get-Content -Raw -LiteralPath $envPath
    if($after -notmatch 'CUSTOM_QUALIFICATION_VALUE=preserve-me'){throw 'La désinstallation a supprimé la configuration utilisateur'}
    Write-Host 'WINDOWS_INSTALLER_E2E=PASS'; Write-Host "INSTALL_DIR=$installDir"; Write-Host "UPGRADE_BACKUP=$backup"
}
finally {
    if($process -and -not $process.HasExited){Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue}
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {$_.ExecutablePath -and ($_.ExecutablePath -eq $fakeDocker -or $_.ExecutablePath -eq $installerLocalDocker)} | ForEach-Object {Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}
    if(Test-Path -LiteralPath $installerLocalDocker){Remove-Item -LiteralPath $installerLocalDocker -Force -ErrorAction SilentlyContinue}
    if(Test-Path -LiteralPath $shortcut){Remove-Item -LiteralPath $shortcut -Force -ErrorAction SilentlyContinue}
}
