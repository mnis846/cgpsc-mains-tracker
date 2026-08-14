@echo off
title Force Stop Desktop Widget
cd /d "%~dp0\.."
echo.
echo This stops Death Star, Vader sticker, and any pythonw desktop widget.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\kill_visible_python.ps1"
echo.
pause