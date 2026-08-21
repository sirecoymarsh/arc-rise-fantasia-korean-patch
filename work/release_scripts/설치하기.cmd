@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0Install-ARF-KO.ps1"
exit /b %errorlevel%
