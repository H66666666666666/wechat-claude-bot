"""测试Claude API"""

import os
import sys
from dotenv import load_dotenv
from claude_api import ClaudeAPI

# 设置标准输出编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()


def main():
    print("=" * 50)
    print("  测试 Claude API")
    print("=" * 50)
    print()

    # 获取配置
    api_key = os.getenv("CLAUDE_API_KEY")
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    if not api_key:
        print("错误：请设置 CLAUDE_API_KEY 环境变量")
        return

    print(f"API Key: {api_key[:20]}...")
    print(f"Model: {model}")
    print()

    # 创建API客户端
    claude = ClaudeAPI(api_key=api_key, model=model)

    # 测试对话
    print("测试对话：")
    print("-" * 50)

    test_messages = [
        "你好",
        "你是谁？",
        "1+1等于几？",
    ]

    user_id = "test_user"

    for msg in test_messages:
        print(f"用户: {msg}")
        reply = claude.chat(user_id, msg)
        print(f"助手: {reply}")
        print()

    print("-" * 50)
    print("测试完成！")


if __name__ == "__main__":
    main()
