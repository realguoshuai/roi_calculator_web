@echo off
chcp 65001 >nul
echo ============================================
echo   ROI Calculator Web - 腾讯云部署版
echo ============================================
echo.
echo 启动服务器: http://localhost:5000
echo 按 Ctrl+C 停止
echo.

cd /d "%~dp0"

pip install -r requirements_web.txt >nul 2>&1

echo 正在启动...
python app.py
