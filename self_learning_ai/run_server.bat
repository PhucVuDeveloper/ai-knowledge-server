@echo off
setlocal
cd /d "%~dp0"
title May Chu AI Central Knowledge Server

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Chua tim thay Python tren may tinh cua ban.
    pause
    exit /b
)

echo [*] Dang kiem tra thu vien FastAPI va Uvicorn...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Dang cai dat thu vien server tu requirements.txt...
    pip install -r requirements.txt
)

echo.
echo =====================================================================
echo    🚀 DANG KHOI CHAY MAY CHU AI CENTRAL KNOWLEDGE BASE
echo =====================================================================
echo [*] May chu dang chay tai: http://localhost:8000
echo [*] Tai lieu API: http://localhost:8000/docs
echo [*] Nhap dia chi 'http://<IP-may-tinh>:8000' tren may khac de ket noi.
echo =====================================================================
echo.

python server.py
pause
