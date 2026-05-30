@echo off
chcp 65001 >nul
echo ========================================
echo   微信 Claude 机器人
echo ========================================
echo.

echo [1/2] 检查依赖...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo 依赖安装失败
    pause
    exit /b 1
)

echo [2/2] 启动机器人...
echo.
python main.py

pause
