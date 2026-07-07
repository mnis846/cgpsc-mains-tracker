# Stop study sticker and Streamlit server processes.
$ErrorActionPreference = "SilentlyContinue"
$patterns = @("*desktop_companion*", "*streamlit*app.py*")
$killed = 0

Get-CimInstance Win32_Process |
    Where-Object {
        $cmd = $_.CommandLine
        $cmd -and ($patterns | Where-Object { $cmd -like $_ })
    } |
    ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force
        Write-Host "Stopped PID $($_.ProcessId)"
        $killed++
    }

if ($killed -eq 0) {
    Write-Host "No tracker processes running."
} else {
    Write-Host "Stopped $killed process(es)."
}