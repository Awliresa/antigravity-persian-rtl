@echo off
chcp 65001 >nul
echo Starting Antigravity RTL Daemon...
start "" /b pythonw "%~dp0daemon\antigravity_rtl_daemon.py"
echo Daemon started in background. You can close this window.
timeout /t 3 >nul
