# Stop study sticker and Streamlit server (not Death Star).
$ErrorActionPreference = "SilentlyContinue"
& (Join-Path $PSScriptRoot "stop_all_tracker.ps1") -TrackerOnly
Write-Host ""
Write-Host "Tip: also right-click the tray icon -> Quit sticker"