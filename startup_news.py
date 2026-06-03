"""开机自启动后自动发送热点新闻"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime

# 设置日志（只输出到文件，不输出到控制台）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("startup_news.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)


def wait_for_openclaw_gateway():
    """等待OpenClaw网关启动"""
    logger.info("等待OpenClaw网关启动...")

    for i in range(60):  # 最多等待60秒
        try:
            result = subprocess.run(
                "openclaw gateway status",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8'
            )
            # 检查输出中是否包含运行状态
            output = result.stdout
            if "Runtime: running" in output or "Connectivity probe: ok" in output:
                logger.info("OpenClaw网关已启动")
                return True
        except Exception as e:
            logger.debug(f"检查网关状态失败: {e}")

        time.sleep(1)

    logger.error("等待OpenClaw网关启动超时")
    return False


def send_news():
    """发送热点新闻"""
    logger.info("开始发送热点新闻...")

    # 使用openclaw cron run命令执行daily-news任务
    try:
        # 先获取任务列表
        result = subprocess.run(
            "openclaw cron list",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8'
        )

        if result.returncode == 0:
            # 查找daily-news任务
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'daily-news' in line and 'bf01ab12' in line:
                    # 提取任务ID
                    parts = line.split()
                    if len(parts) > 0:
                        task_id = parts[0]
                        logger.info(f"找到daily-news任务: {task_id}")

                        # 执行任务
                        run_result = subprocess.run(
                            f"openclaw cron run {task_id}",
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=60,
                            encoding='utf-8'
                        )

                        if run_result.returncode == 0:
                            logger.info("热点新闻任务已执行")
                            return True
                        else:
                            logger.error(f"执行任务失败: {run_result.stderr}")
                            return False

        # 如果上面的方法失败，直接使用openclaw message send发送消息
        logger.info("使用备用方案发送消息...")

        # 获取热点新闻
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from daily_news import get_hot_news, format_news_message

        news_list = get_hot_news()
        message = format_news_message(news_list)

        # 发送消息
        cmd = f'openclaw message send --channel openclaw-weixin --target "o9cq80zOJNAxg1j5JcyFfH4KEzqk@im.wechat" --message "{message}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8')

        if result.returncode == 0:
            logger.info("热点新闻已发送")
            return True
        else:
            logger.error(f"发送消息失败: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"发送热点新闻失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("  开机自启动发送热点新闻")
    logger.info("=" * 50)

    # 等待OpenClaw网关启动
    if not wait_for_openclaw_gateway():
        logger.error("OpenClaw网关未启动，无法发送新闻")
        sys.exit(1)

    # 等待一段时间让网关完全初始化
    logger.info("等待网关完全初始化...")
    time.sleep(10)

    # 发送热点新闻
    if send_news():
        logger.info("热点新闻发送完成！")
    else:
        logger.error("热点新闻发送失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
