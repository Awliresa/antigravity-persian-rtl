@echo off
chcp 65001 >nul
echo.
echo Removing Antigravity RTL Daemon from Windows Startup...
python "%~dp0daemon\antigravity_rtl_daemon.py" --uninstall

:: کشتن هر نمونه در حال اجرا
taskkill /f /im pythonw.exe /fi "WINDOWTITLE eq antigravity_rtl_daemon*" >nul 2>&1
echo Done.
pause
