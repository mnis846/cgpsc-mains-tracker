# Stop study sticker and Streamlit server processes.
$ErrorActionPreference = "SilentlyContinue"
& (Join-Path $PSScriptRoot "stop_all_tracker.ps1")
Write-Host ""
Write-Host "Tip: also right-click the tray icon -> Quit sticker"