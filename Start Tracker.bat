@echo off
title CGPSC Mains Tracker
cd /d "%~dp0"

echo Stopping any old sticker first...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_all_tracker.ps1" >nul 2>&1
echo Starting CGPSC Mains Tracker + Study Coach...
for /f "delims=" %%P in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\resolve_python.ps1" -Gui') do set "PY=%%P"
if not defined PY (
    echo Python not found. Install Python 3.10+ and run: pip install -r requirements.txt
    pause
    exit /b 1
)
start "" /min "%PY%" "%~dp0desktop_companion.py"
echo Study sticker + website will open in a few seconds.
echo If nothing appears, check tracker-launch.log in this folder.
exit /b 0