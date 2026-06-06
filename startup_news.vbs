Set objShell = CreateObject("WScript.Shell")
objShell.CurrentDirectory = "D:\first-cc\wechat-claude-bot"
objShell.Run "cmd /c pythonw run_news_silent.py", 0, True
