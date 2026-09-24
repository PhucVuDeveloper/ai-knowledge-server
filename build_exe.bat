@echo off
setlocal
cd /d "%~dp0"
title Dong Goi Ung Dung Tro Ly AI Tu Dong Cap Nhat (Dynamic Loader)

echo =====================================================================
echo    📦 DONG GOI UNG DUNG TRO LY AI THANH FILE EXE TU DONG CAP NHAT
echo =====================================================================
echo [*] Ung dung sau khi dong goi se tu dong cap nhat giao dien va tinh nang
echo     moi nhat tu server ma KHONG can phai dong goi hay gui lai file .exe!
echo [*] Nguoi dung chi can nhap dup chuot la dung ngay tren moi may Windows.
echo =====================================================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Chua tim thay Python tren may tinh de thuc hien dong goi.
    pause
    exit /b
)

echo [*] Dang kiem tra cong cu PyInstaller...
python -m pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Dang cai dat PyInstaller...
    python -m pip install pyinstaller
)

echo.
echo [*] Dang tien hanh dong goi thanh file TroLyAI.exe (Vui long doi 1-2 phut)...
python -m PyInstaller --noconsole --onefile --name "TroLyAI" --clean ^
    --add-data "app_floating_ai.py;." ^
    --add-data "chatbot.py;." ^
    --add-data "cloud_client.py;." ^
    --add-data "knowledge_base.json;." ^
    --add-data "server_config.json;." ^
    launcher.py

if %errorlevel% equ 0 (
    echo.
    echo =====================================================================
    echo [OK] DONG GOI THANH CONG!
    echo [*] File ung dung doc lap da duoc tao tai:
    echo     %~dp0dist\TroLyAI.exe
    echo.
    echo [*] BAN CHI CAN GUI FILE TroLyAI.exe NAY CHO NGUOI DUNG DUNG 1 LAN DUY NHAT!
    echo [*] Sau nay khi ban sua app_floating_ai.py tren GitHub / Render:
    echo     Moi may client khi mo TroLyAI.exe se TU DONG TAI GIAO DIEN MOI VE!
    echo =====================================================================
) else (
    echo.
    echo [!] Da xay ra loi trong qua trinh dong goi.
)

pause
