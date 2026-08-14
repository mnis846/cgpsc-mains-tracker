# Start the Godot garden FastAPI bridge on port 8000.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$py = Join-Path $Root "venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    $py = "python"
}

Write-Host "Starting Study Garden API at http://127.0.0.1:8000 ..."
Write-Host "Endpoint: GET /api/garden/milestones"
& $py -m uvicorn garden_api:app --reload --host 127.0.0.1 --port 8000
