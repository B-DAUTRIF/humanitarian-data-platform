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
if (Test-Path -LiteralPath $work) { Remove-Item -LiteralPath $work -Recurse -Force }
New-Item -ItemType Directory -Force -Path $fakeBin | Out-Null

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
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern IntPtr GetDlgItem(IntPtr hWnd, int nIDDlgItem);
    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);
    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetClassName(IntPtr hWnd, StringBuilder lpClassName, int nMaxCount);
    [DllImport("user32.dll", EntryPoint = "SendMessageW")]
    public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
    [DllImport("user32.dll", CharSet = CharSet.Unicode, EntryPoint = "SendMessageW")]
    public static extern IntPtr SendMessageGetText(IntPtr hWnd, uint Msg, IntPtr wParam, StringBuilder lParam);
    [DllImport("user32.dll", CharSet = CharSet.Unicode, EntryPoint = "SendMessageW")]
    public static extern IntPtr SendMessageSetText(IntPtr hWnd, uint Msg, IntPtr wParam, string lParam);
    [DllImport("user32.dll")]
    public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);

    public static IntPtr FindDialogForProcess(uint processId) {
        IntPtr found = IntPtr.Zero;
        EnumWindows(delegate(IntPtr hWnd, IntPtr lParam) {
            uint pid;
            GetWindowThreadProcessId(hWnd, out pid);
            if (pid != processId) return true;
            StringBuilder name = new StringBuilder(256);
            GetClassName(hWnd, name, name.Capacity);
            if (name.ToString() == "#32770") {
                found = hWnd;
                return false;
            }
            return true;
        }, IntPtr.Zero);
        return found;
    }
}
'@

$WM_SETTEXT = 0x000C
$WM_GETTEXT = 0x000D
$BM_CLICK = 0x00F5
$BM_SETCHECK = 0x00F1
$BST_UNCHECKED = 0
$BST_CHECKED = 1
$IDYES = 6
$IDOK = 1
$script:healthProcess = $null

function Wait-MainWindow([System.Diagnostics.Process]$Process, [int]$TimeoutSeconds = 30) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        Start-Sleep -Milliseconds 250
        $Process.Refresh()
        if ($Process.HasExited) { throw "L'installateur s'est arrêté prématurément: $($Process.ExitCode)" }
        if ($Process.MainWindowHandle -ne [IntPtr]::Zero) { return $Process.MainWindowHandle }
    } while ((Get-Date) -lt $deadline)
    throw 'Fenêtre principale de l installateur introuvable'
}

function Get-Control([IntPtr]$Window, [int]$Id) {
    $control = [HDPWin32]::GetDlgItem($Window, $Id)
    if ($control -eq [IntPtr]::Zero) { throw "Contrôle Windows ID=$Id introuvable" }
    return $control
}

function Set-ControlText([IntPtr]$Window, [int]$Id, [string]$Value) {
    $control = Get-Control $Window $Id
    [void][HDPWin32]::SendMessageSetText($control, $WM_SETTEXT, [IntPtr]::Zero, $Value)
}

function Get-ControlText([IntPtr]$Window, [int]$Id) {
    $control = Get-Control $Window $Id
    $buffer = New-Object System.Text.StringBuilder 4096
    [void][HDPWin32]::SendMessageGetText($control, $WM_GETTEXT, [IntPtr]$buffer.Capacity, $buffer)
    return $buffer.ToString()
}

function Wait-ControlText([IntPtr]$Window, [int]$Id, [int]$TimeoutSeconds = 10) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $value = Get-ControlText $Window $Id
        if ($value) { return $value }
        Start-Sleep -Milliseconds 100
    } while ((Get-Date) -lt $deadline)
    throw "Contrôle ID=$Id non initialisé dans le délai attendu"
}

function Set-Check([IntPtr]$Window, [int]$Id, [bool]$Checked) {
    $control = Get-Control $Window $Id
    $value = if ($Checked) { $BST_CHECKED } else { $BST_UNCHECKED }
    [void][HDPWin32]::SendMessage($control, $BM_SETCHECK, [IntPtr]$value, [IntPtr]::Zero)
}

function Click-Control([IntPtr]$Window, [int]$Id) {
    $control = Get-Control $Window $Id
    if (-not [HDPWin32]::PostMessage($control, $BM_CLICK, [IntPtr]::Zero, [IntPtr]::Zero)) { throw "PostMessage BM_CLICK ID=$Id a échoué" }
}

function Click-DialogButton([int]$ProcessId, [int]$Id, [int]$TimeoutSeconds = 20) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $dialog = [HDPWin32]::FindDialogForProcess([uint32]$ProcessId)
        if ($dialog -ne [IntPtr]::Zero) {
            $button = [HDPWin32]::GetDlgItem($dialog, $Id)
            if ($button -ne [IntPtr]::Zero) {
                if (-not [HDPWin32]::PostMessage($button, $BM_CLICK, [IntPtr]::Zero, [IntPtr]::Zero)) { throw "PostMessage dialogue ID=$Id a échoué" }
                Start-Sleep -Milliseconds 250
                return
            }
        }
        Start-Sleep -Milliseconds 200
    } while ((Get-Date) -lt $deadline)
    throw "Dialogue du processus $ProcessId avec bouton ID=$Id introuvable"
}

function Dismiss-InformationalDialog([int]$ProcessId, [int]$TimeoutSeconds = 2) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $dialog = [HDPWin32]::FindDialogForProcess([uint32]$ProcessId)
        if ($dialog -ne [IntPtr]::Zero) {
            $button = [HDPWin32]::GetDlgItem($dialog, $IDOK)
            if ($button -ne [IntPtr]::Zero) {
                [void][HDPWin32]::PostMessage($button, $BM_CLICK, [IntPtr]::Zero, [IntPtr]::Zero)
                Write-Host 'INFORMATIONAL_DIALOG_DISMISSED=YES'
                Start-Sleep -Milliseconds 250
                return
            }
        }
        Start-Sleep -Milliseconds 100
    } while ((Get-Date) -lt $deadline)
    Write-Host 'INFORMATIONAL_DIALOG_DISMISSED=NOT_EXPOSED_BY_RUNNER'
}

function Ensure-ControlledHealthServer {
    if ($script:healthProcess -and -not $script:healthProcess.HasExited) { return }
    $envPath = Join-Path $installDir '.env'
    if (-not (Test-Path -LiteralPath $envPath)) { return }
    $line = Get-Content -LiteralPath $envPath | Where-Object { $_ -match '^HDP_PORT=\d+$' } | Select-Object -First 1
    if (-not $line) { return }
    $port = [int]($line -replace '^HDP_PORT=', '')
    $script:healthProcess = Start-Process -FilePath $fakeDocker -ArgumentList @('--health-server', "$port") -PassThru -WindowStyle Hidden
    Start-Sleep -Milliseconds 400
    if ($script:healthProcess.HasExited) { throw "Serveur de santé contrôlé interrompu: $($script:healthProcess.ExitCode)" }
    Write-Host "CONTROLLED_HEALTH_SERVER=127.0.0.1:$port"
}

function Wait-Status([IntPtr]$Window, [string]$Needle, [int]$TimeoutSeconds = 240) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $last = ''
    do {
        Ensure-ControlledHealthServer
        $last = Get-ControlText $Window 1011
        if ($last -like "*$Needle*") { return $last }
        if ($last -like '*interrompue*' -or $last -like '*annulée*') { throw "Statut d'échec détecté: $last" }
        Start-Sleep -Milliseconds 400
    } while ((Get-Date) -lt $deadline)
    throw "Délai dépassé en attente du statut '$Needle'. Dernier statut: $last"
}

function Assert-File([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Fichier attendu absent: $Path" }
}

$desktop = [Environment]::GetFolderPath('Desktop')
$shortcut = Join-Path $desktop 'Humanitarian Data Platform.lnk'
$process = $null
try {
    $process = Start-Process -FilePath $installerResolved -PassThru
    $window = Wait-MainWindow $process
    [void](Wait-ControlText $window 1001)

    Set-ControlText $window 1001 $installDir
    Set-ControlText $window 1002 'hdp-ci-qualification'
    Set-ControlText $window 1014 ''
    Set-Check $window 1013 $true
    if ((Get-ControlText $window 1001) -ne $installDir) { throw 'Le chemin de recette n a pas été appliqué à la GUI' }
    if ((Get-ControlText $window 1002) -ne 'hdp-ci-qualification') { throw 'L appname ReliefWeb de recette n a pas été appliqué' }

    Click-Control $window 1007
    Click-DialogButton $process.Id $IDYES
    $status = Wait-Status $window 'Installation terminée'
    Dismiss-InformationalDialog $process.Id

    Assert-File (Join-Path $installDir 'compose.yaml')
    Assert-File (Join-Path $installDir 'start-hdp.cmd')
    Assert-File (Join-Path $installDir 'start-hdp-with-r.cmd')
    Assert-File (Join-Path $installDir '.env')
    Assert-File (Join-Path $installDir '.hdp-managed-installation')
    Assert-File $shortcut

    $envPath = Join-Path $installDir '.env'
    $envText = Get-Content -Raw -LiteralPath $envPath
    if ($envText -notmatch '(?m)^HDP_AUTH_MODE=passkey\s*$') { throw 'HDP_AUTH_MODE=passkey absent de .env' }
    if ($envText -notmatch '(?m)^HDP_PORT=\d+\s*$') { throw 'HDP_PORT absent de .env' }
    if ($envText -notmatch '(?m)^RELIEFWEB_APPNAME=hdp-ci-qualification\s*$') { throw 'Appname ReliefWeb de la GUI absent de .env' }
    Add-Content -LiteralPath $envPath -Value "CUSTOM_QUALIFICATION_VALUE=preserve-me"

    Click-Control $window 1007
    Click-DialogButton $process.Id $IDYES
    $status = Wait-Status $window 'Installation terminée'
    Dismiss-InformationalDialog $process.Id

    $backup = Join-Path $installDir '.env.backup-before-v6.0.0'
    Assert-File $backup
    $current = Get-Content -Raw -LiteralPath $envPath
    $previous = Get-Content -Raw -LiteralPath $backup
    if ($current -notmatch 'CUSTOM_QUALIFICATION_VALUE=preserve-me') { throw 'La mise à niveau a perdu une variable utilisateur' }
    if ($previous -notmatch 'CUSTOM_QUALIFICATION_VALUE=preserve-me') { throw 'La sauvegarde .env ne contient pas la valeur utilisateur' }
    Assert-File $shortcut

    Click-Control $window 1016
    Click-DialogButton $process.Id $IDYES
    $status = Wait-Status $window 'Désinstallation terminée'
    Dismiss-InformationalDialog $process.Id
    Assert-File $envPath
    Assert-File $backup
    if (Test-Path -LiteralPath $shortcut) { throw 'Le raccourci HDP est resté après désinstallation contrôlée' }
    if (Test-Path -LiteralPath (Join-Path $installDir '.hdp-managed-installation')) { throw 'Le marqueur géré est resté après désinstallation' }
    if (Test-Path -LiteralPath (Join-Path $installDir 'compose.yaml')) { throw 'Le payload géré est resté après désinstallation' }
    $after = Get-Content -Raw -LiteralPath $envPath
    if ($after -notmatch 'CUSTOM_QUALIFICATION_VALUE=preserve-me') { throw 'La désinstallation a supprimé la configuration utilisateur' }

    Write-Host 'WINDOWS_INSTALLER_E2E=PASS'
    Write-Host "INSTALL_DIR=$installDir"
    Write-Host "UPGRADE_BACKUP=$backup"
}
finally {
    if ($process -and -not $process.HasExited) { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue }
    if ($script:healthProcess -and -not $script:healthProcess.HasExited) { Stop-Process -Id $script:healthProcess.Id -Force -ErrorAction SilentlyContinue }
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ExecutablePath -and ($_.ExecutablePath -eq $fakeDocker -or $_.ExecutablePath -eq $installerLocalDocker) } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $installerLocalDocker) { Remove-Item -LiteralPath $installerLocalDocker -Force -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $shortcut) { Remove-Item -LiteralPath $shortcut -Force -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $work) { Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue }
}
