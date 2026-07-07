# One-click launcher - double-click "Start Tracker.bat" or run this script.
$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

$Port = 8501
$Url = "http://localhost:$Port"
$LogFile = Join-Path $ProjectRoot "tracker-launch.log"

function Write-Log([string]$Message) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $Message"
    Add-Content -Path $LogFile -Value $line
    Write-Host $Message
}

function Test-PortOpen([int]$TargetPort) {
    try {
        $conn = Get-NetTCPConnection -LocalPort $TargetPort -State Listen -ErrorAction SilentlyContinue
        return [bool]$conn
    } catch {
        return $false
    }
}

function Resolve-Python {
    $resolved = & (Join-Path $PSScriptRoot "resolve_python.ps1")
    if ($LASTEXITCODE -eq 0) { return $resolved }
    return $null
}

function Wait-ForServer([int]$TargetPort, [string]$TargetUrl, [string]$ReadyMessage) {
    $joinDeadline = (Get-Date).AddSeconds(45)
    while ((Get-Date) -lt $joinDeadline) {
        if (Test-PortOpen $TargetPort) {
            Start-Sleep -Seconds 1
            Start-Process $TargetUrl
            Write-Log $ReadyMessage
            return $true
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

Write-Log "Launch requested from $ProjectRoot"

if (Test-PortOpen $Port) {
    Write-Log "Server already on port $Port - opening browser"
    Start-Process $Url
    exit 0
}

# Prevent two launchers (e.g. startup race) from starting duplicate servers.
$LockFile = Join-Path $ProjectRoot ".tracker-launch.lock"
$LockStream = $null
$OwnsLaunchLock = $false
$exitCode = 0

try {
    try {
        $LockStream = [System.IO.File]::Open(
            $LockFile,
            [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::Write,
            [System.IO.FileShare]::None
        )
        $OwnsLaunchLock = $true
    } catch [System.IO.IOException] {
        Write-Log "Another launch in progress - waiting for server"
        if (Wait-ForServer $Port $Url "Joined existing launch at $Url") { exit 0 }
        Write-Log "ERROR: Timed out waiting for server started by another launcher"
        exit 1
    }

    $pythonCmd = Resolve-Python
    if (-not $pythonCmd) {
        Write-Log "ERROR: Python not found in PATH"
        Write-Host ""
        Write-Host "Python not found. Install Python 3.10+ then run:"
        Write-Host "  pip install -r requirements.txt"
        $exitCode = 1
    } else {
        Write-Log "Using Python: $pythonCmd"
        Write-Log "Starting Streamlit..."

        if ($pythonCmd -like "* -3") {
            $parts = $pythonCmd -split " ", 2
            $exe = $parts[0]
            $argPrefix = @($parts[1])
        } else {
            $exe = $pythonCmd
            $argPrefix = @()
        }

        $streamlitArgs = $argPrefix + @(
            "-m", "streamlit", "run", "app.py",
            "--server.headless", "true",
            "--server.port", "$Port"
        )

        Start-Process -FilePath $exe `
            -ArgumentList $streamlitArgs `
            -WorkingDirectory $ProjectRoot `
            -WindowStyle Minimized | Out-Null

        if (-not (Wait-ForServer $Port $Url "Ready at $Url")) {
            Write-Log "ERROR: Server did not start within 45 seconds"
            Write-Host ""
            Write-Host "Server did not start. Try manually:"
            Write-Host "  cd $ProjectRoot"
            Write-Host "  python -m streamlit run app.py"
            Write-Host ""
            Write-Host "Log: $LogFile"
            $exitCode = 1
        }
    }
} finally {
    if ($LockStream) {
        $LockStream.Dispose()
    }
    if ($OwnsLaunchLock -and (Test-Path $LockFile)) {
        Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
    }
}

exit $exitCode