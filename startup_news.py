"""开机自启动后自动发送热点新闻"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime
import ctypes

# 隐藏控制台窗口
def hide_console():
    """隐藏控制台窗口"""
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

# 隐藏控制台窗口
hide_console()

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

    # 先发送一条消息获取contextToken
    try:
        logger.info("先发送一条消息获取contextToken...")
        cmd = 'openclaw message send --channel openclaw-weixin --target "o9cq80zOJNAxg1j5JcyFfH4KEzqk@im.wechat" --message "📰 正在获取今日热点新闻..."'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8')
        if result.returncode == 0:
            logger.info("contextToken获取成功")
            time.sleep(3)  # 等待contextToken生效
        else:
            logger.warning(f"contextToken获取失败: {result.stderr}")
    except Exception as e:
        logger.warning(f"contextToken获取异常: {e}")

    # 直接获取新闻并分多条短消息发送
    try:
        logger.info("获取热点新闻...")
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from daily_news import get_hot_news

        news_list = get_hot_news()
        if not news_list:
            logger.error("获取热点新闻失败")
            return False

        logger.info(f"获取到 {len(news_list)} 条热点新闻")

        today = datetime.now().strftime("%Y年%m月%d日")

        # 逐条发送新闻，每条单独发送
        for i, news in enumerate(news_list[:10], 1):
            title = news.get("name", "")
            if len(title) > 40:
                title = title[:40] + "..."

            if i == 1:
                msg = f"📰 {today} 热点新闻\n{i}. {title}"
            else:
                msg = f"{i}. {title}"

            logger.info(f"发送第{i}条: {msg[:50]}...")
            cmd = f'openclaw message send --channel openclaw-weixin --target "o9cq80zOJNAxg1j5JcyFfH4KEzqk@im.wechat" --message "{msg}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8')

            if result.returncode == 0:
                logger.info(f"第{i}条新闻已发送")
            else:
                logger.error(f"第{i}条新闻发送失败: {result.stderr}")

            time.sleep(2)  # 每条间隔2秒

        # 发送数据来源
        logger.info("发送数据来源...")
        cmd = 'openclaw message send --channel openclaw-weixin --target "o9cq80zOJNAxg1j5JcyFfH4KEzqk@im.wechat" --message "数据来源: 知乎热榜 / GitHub Trending"'
        subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8')

        logger.info("热点新闻发送完成！")
        return True

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
