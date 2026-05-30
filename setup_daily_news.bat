@echo off
chcp 65001 >nul
echo ========================================
echo   设置开机自动发送热点新闻
echo ========================================
echo.

echo [1/2] 创建计划任务（登录时触发）...
schtasks /Create /TN "DailyNews" /TR "python D:\first-cc\wechat-claude-bot\daily_news.py" /SC ONLOGON /DELAY 0001:00 /F
if errorlevel 1 (
    echo 创建计划任务失败
    pause
    exit /b 1
)

echo [2/2] 启用计划任务...
schtasks /Change /TN "DailyNews" /ENABLE

echo.
echo ========================================
echo   设置完成！
echo   每次开机登录后1分钟自动发送热点新闻
echo ========================================
echo.
pause
