@echo off
echo ============================================
echo    GM打卡日志 - 启动中...
echo ============================================
echo.
echo 访问地址: http://localhost:5001
echo.
echo 按 Ctrl+C 停止服务器
echo ============================================
echo.

cd /d "%~dp0"
python app.py

pause
