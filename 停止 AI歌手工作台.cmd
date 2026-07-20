@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0scripts\stop-workbench.ps1"
exit /b %errorlevel%
