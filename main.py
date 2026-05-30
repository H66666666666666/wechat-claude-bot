"""微信Claude机器人 - 主程序"""

import os
import sys
import time
import signal
import logging
from typing import Dict, Set

from config import (
    WEIXIN_API_BASE_URL,
    WEIXIN_TOKEN,
    CLAUDE_API_KEY,
    CLAUDE_MODEL,
    CLAUDE_MAX_TOKENS,
    SYSTEM_PROMPT,
)
from weixin_api import WeixinAPI, WeixinMessage
from claude_api import ClaudeAPI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)


class WeixinClaudeBot:
    """微信Claude机器人"""

    def __init__(self):
        # 初始化微信API
        self.weixin = WeixinAPI(WEIXIN_API_BASE_URL, WEIXIN_TOKEN)

        # 初始化Claude API
        self.claude = ClaudeAPI(
            api_key=CLAUDE_API_KEY,
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
        )

        # 已处理的消息ID（防止重复处理）
        self.processed_messages: Set[int] = set()

        # 运行状态
        self.running = False

    def start(self):
        """启动机器人"""
        logger.info("=" * 50)
        logger.info("  微信 Claude 机器人")
        logger.info("=" * 50)
        logger.info("")

        # 检查配置
        if not CLAUDE_API_KEY:
            logger.error("请设置 CLAUDE_API_KEY 环境变量")
            sys.exit(1)

        if not WEIXIN_TOKEN:
            logger.error("请设置 WEIXIN_TOKEN 环境变量")
            sys.exit(1)

        # 通知服务端启动
        logger.info("正在连接微信服务...")
        if self.weixin.notify_start():
            logger.info("✓ 已连接到微信服务")
        else:
            logger.warning("⚠ 连接微信服务失败，继续尝试...")

        logger.info("")
        logger.info("机器人已启动，等待消息...")
        logger.info("按 Ctrl+C 退出")
        logger.info("")

        self.running = True

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # 主循环
        self._run_loop()

    def _run_loop(self):
        """主循环"""
        while self.running:
            try:
                # 获取新消息
                messages = self.weixin.get_updates(timeout_ms=35000)

                for msg in messages:
                    self._process_message(msg)

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"主循环错误: {e}")
                time.sleep(5)

        self._shutdown()

    def _process_message(self, msg: WeixinMessage):
        """处理消息"""
        # 跳过已处理的消息
        if msg.message_id in self.processed_messages:
            return

        # 跳过机器人自己的消息
        if msg.is_bot_message:
            return

        # 跳过空消息
        text = msg.text.strip()
        if not text:
            return

        # 记录已处理
        self.processed_messages.add(msg.message_id)

        # 保持已处理消息集合大小
        if len(self.processed_messages) > 10000:
            self.processed_messages = set(list(self.processed_messages)[-5000:])

        user_id = msg.from_user_id
        logger.info(f"收到消息 [{user_id}]: {text}")

        # 处理特殊命令
        if text.lower() in ["/clear", "/reset", "清除记录", "重置对话"]:
            self.claude.clear_history(user_id)
            self.weixin.send_message(user_id, "✓ 对话记录已清除", msg.context_token)
            logger.info(f"已清除用户 {user_id} 的对话记录")
            return

        if text.lower() in ["/help", "帮助"]:
            help_text = """🤖 微信 Claude 机器人

使用方法：
• 直接发送消息即可对话
• 支持多轮对话，自动保持上下文

命令：
• /clear - 清除对话记录
• /help - 显示此帮助信息

特点：
• 基于 Claude AI，智能回答问题
• 支持中英文对话
• 记住对话上下文"""
            self.weixin.send_message(user_id, help_text, msg.context_token)
            return

        # 调用Claude API
        try:
            reply = self.claude.chat(user_id, text, SYSTEM_PROMPT)
            logger.info(f"Claude回复 [{user_id}]: {reply[:100]}...")

            # 发送回复
            success = self.weixin.send_message(user_id, reply, msg.context_token)
            if success:
                logger.info(f"✓ 回复已发送")
            else:
                logger.error(f"✗ 回复发送失败")

        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            error_msg = "抱歉，处理您的消息时出现错误，请稍后再试。"
            self.weixin.send_message(user_id, error_msg, msg.context_token)

    def _signal_handler(self, signum, frame):
        """信号处理"""
        logger.info("\n正在停止机器人...")
        self.running = False

    def _shutdown(self):
        """关闭"""
        logger.info("正在断开连接...")
        self.weixin.notify_stop()
        logger.info("机器人已停止")


def main():
    bot = WeixinClaudeBot()
    bot.start()


if __name__ == "__main__":
    main()
