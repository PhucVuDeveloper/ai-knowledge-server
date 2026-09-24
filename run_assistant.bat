@echo off
setlocal
cd /d "%~dp0"
title Tro Ly AI Tu Hoc

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Chua tim thay Python tren may tinh cua ban.
    echo [*] Dang khoi chay trinh cai dat Python qua winget...
    echo.
    winget install Python.Python.3.11
    echo.
    echo [*] Neu cai dat xong, hay khoi dong lai tep nay.
    pause
    exit /b
)

echo [*] Dang khoi chay Tro ly AI...
python app_floating_ai.py
if %errorlevel% neq 0 (
    echo.
    echo [!] Co loi xay ra khi chay ung dung.
    pause
)
