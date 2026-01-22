@echo off
chcp 65001 >nul
title ROI Calculator Web - 本地测试
echo ============================================
echo   ROI Calculator Web - 本地测试
echo ============================================
echo.

cd /d "%~dp0"

echo [1/4] 检查依赖...
pip install -r requirements_web.txt >nul 2>&1
if %errorlevel% equ 0 (
    echo     ✅ 依赖安装完成
) else (
    echo     ❌ 依赖安装失败
    pause
    exit /b 1
)

echo.
echo [2/4] 启动服务器...
echo.
echo     访问地址: http://localhost:5000
echo     按 Ctrl+C 停止服务器
echo.
echo ============================================

python app.py
