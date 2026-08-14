# Pin CGPSC Tracker + Study Coach to Windows Startup (runs on login).
# Usage:
#   powershell -File scripts\install_startup.ps1           # enable (default)
#   powershell -File scripts\install_startup.ps1 -Remove   # disable
#   powershell -File scripts\install_startup.ps1 -Status   # check
param(
    [switch]$Remove,
    [switch]$Status
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$Launcher = Join-Path $ProjectRoot "Start Tracker.bat"
$Startup = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $Startup "CGPSC Mains Tracker.lnk"

# Older project names that also auto-started and caused a double launch on login.
$LegacyShortcutNames = @(
    "Study Routine Tracker.lnk"
)

function Remove-LegacyStartupShortcuts {
    foreach ($name in $LegacyShortcutNames) {
        $path = Join-Path $Startup $name
        if (Test-Path -LiteralPath $path) {
            Remove-Item -LiteralPath $path -Force
            Write-Host "Removed legacy startup shortcut (prevents double launch):"
            Write-Host "  $path"
        }
    }
}

function Test-Installed {
    return Test-Path -LiteralPath $ShortcutPath
}

if ($Status) {
    if (Test-Installed) {
        Write-Host "Autostart: ON"
        Write-Host "  $ShortcutPath"
    } else {
        Write-Host "Autostart: OFF"
    }
    foreach ($name in $LegacyShortcutNames) {
        $path = Join-Path $Startup $name
        if (Test-Path -LiteralPath $path) {
            Write-Host "WARNING: legacy startup still present (causes double launch):"
            Write-Host "  $path"
        }
    }
    exit 0
}

if ($Remove) {
    Remove-LegacyStartupShortcuts
    if (Test-Installed) {
        Remove-Item -LiteralPath $ShortcutPath -Force
        Write-Host "Autostart removed."
        Write-Host "The tracker will no longer start when Windows logs in."
    } else {
        Write-Host "Autostart was not installed (nothing to remove)."
    }
    exit 0
}

if (-not (Test-Path $Launcher)) {
    Write-Error "Launcher not found: $Launcher"
}

# Always strip old Study Routine Tracker (and similar) entries first.
Remove-LegacyStartupShortcuts

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Launcher
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.WindowStyle = 7  # Minimized
$Shortcut.Description = "CGPSC Mains Tracker + Study Coach"
$Shortcut.Save()

Write-Host "Startup shortcut installed:"
Write-Host "  $ShortcutPath"
Write-Host ""
Write-Host "On every login: Streamlit app + always-on-top study sticker (top-right)."
Write-Host "To remove: powershell -File scripts\install_startup.ps1 -Remove"
Write-Host "  or delete that shortcut from your Startup folder."
