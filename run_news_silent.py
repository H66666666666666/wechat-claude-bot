"""静默运行热点新闻推送"""

import os
import sys
import subprocess
import ctypes

# 隐藏控制台窗口
def hide_console():
    """隐藏控制台窗口"""
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

# 设置工作目录
os.chdir(r"D:\first-cc\wechat-claude-bot")

# 隐藏控制台窗口
hide_console()

# 运行startup_news.py
try:
    subprocess.run(
        [sys.executable, "startup_news.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
except:
    pass
