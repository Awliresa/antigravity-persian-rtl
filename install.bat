@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║     Antigravity Persian RTL Daemon — Installer           ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

:: پیدا کردن python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

:: نصب daemon در Startup
echo [1/2] Installing daemon to Windows Startup...
python "%~dp0daemon\antigravity_rtl_daemon.py" --install
if %errorlevel% neq 0 (
    echo [ERROR] Installation failed.
    pause
    exit /b 1
)

:: اجرای فوری daemon
echo.
echo [2/2] Starting daemon now (background)...
start "" /b pythonw "%~dp0daemon\antigravity_rtl_daemon.py"

echo.
echo ✓ Installation complete!
echo   The daemon will auto-start with Windows.
echo   Make sure Google Antigravity is open to see the effect.
echo.
pause
