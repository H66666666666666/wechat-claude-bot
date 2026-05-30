"""Claude API客户端 - 支持Claude和MiMo兼容API"""

import os
import logging
from typing import List, Dict, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

# MiMo API配置
MIMO_BASE_URL = os.getenv("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1")


class ClaudeAPI:
    """Claude API客户端（使用OpenAI兼容格式）"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", max_tokens: int = 4096):
        # 判断是否使用MiMo API
        if "mimo" in model.lower():
            self.client = OpenAI(
                api_key=api_key,
                base_url=MIMO_BASE_URL + "/",
            )
        else:
            # Claude API使用OpenAI兼容格式
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.anthropic.com/v1/",
            )

        self.model = model
        self.max_tokens = max_tokens
        # 会话历史（按用户ID存储）
        self.conversations: Dict[str, List[Dict[str, str]]] = {}

    def chat(self, user_id: str, message: str, system_prompt: str = "") -> str:
        """发送消息并获取回复"""
        # 获取或创建会话历史
        if user_id not in self.conversations:
            self.conversations[user_id] = []

        # 添加用户消息
        self.conversations[user_id].append({
            "role": "user",
            "content": message
        })

        # 保持会话历史在合理范围内（最多20轮对话）
        if len(self.conversations[user_id]) > 40:
            self.conversations[user_id] = self.conversations[user_id][-40:]

        try:
            # 构建消息列表
            messages = []

            # 添加系统提示词
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            # 添加对话历史
            messages.extend(self.conversations[user_id])

            # 调用API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
            )

            # 提取回复
            reply = response.choices[0].message.content

            # 添加助手回复到历史
            self.conversations[user_id].append({
                "role": "assistant",
                "content": reply
            })

            return reply

        except Exception as e:
            logger.error(f"API error: {e}")
            # 移除失败的用户消息
            if self.conversations[user_id]:
                self.conversations[user_id].pop()
            return f"抱歉，处理消息时出错：{str(e)}"

    def clear_history(self, user_id: str):
        """清除用户会话历史"""
        if user_id in self.conversations:
            del self.conversations[user_id]

    def get_history(self, user_id: str) -> List[Dict[str, str]]:
        """获取用户会话历史"""
        return self.conversations.get(user_id, [])
