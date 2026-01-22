@echo off
chcp 65001 >nul
title ROI Calculator Web

echo ============================================
echo   ROI Calculator Web - 投资回报率分析工具
echo ============================================
echo.
echo 访问地址: http://localhost:5000
echo 按 Ctrl+C 停止服务
echo.

cd /d "%~dp0"

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查并安装依赖
echo [1/3] 检查依赖...
pip install -r requirements_web.txt >nul 2>&1
if errorlevel 1 (
    echo [WARN] 依赖安装可能有警告，继续尝试启动...
)

echo [2/3] 清理旧进程...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 1 /nobreak >nul

echo [3/3] 启动服务...
echo.
echo ============================================
python app.py
