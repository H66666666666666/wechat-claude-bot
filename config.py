"""配置文件"""

import os
from dotenv import load_dotenv

load_dotenv()

# 微信API配置
WEIXIN_API_BASE_URL = os.getenv("WEIXIN_API_BASE_URL", "https://ilink.weixin.qq.com/cgi-bin/")
WEIXIN_TOKEN = os.getenv("WEIXIN_TOKEN", "")

# Claude API配置
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))

# 系统提示词
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", """你是一个智能助手，请用中文回答问题。保持简洁、友好、有帮助。""")
