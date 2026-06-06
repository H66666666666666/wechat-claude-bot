"""开机自启动后自动发送热点新闻"""

import os
import sys
import time
import subprocess
import logging
import json
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


def check_context_token():
    """检查contextToken是否有效"""
    try:
        token_file = os.path.expanduser("~/.openclaw/openclaw-weixin/accounts/b8f511d5f019-im-bot.context-tokens.json")
        if not os.path.exists(token_file):
            logger.warning("contextToken文件不存在")
            return False

        with open(token_file, 'r', encoding='utf-8') as f:
            tokens = json.load(f)

        if not tokens:
            logger.warning("contextToken为空")
            return False

        logger.info(f"contextToken存在，共{len(tokens)}个")
        return True
    except Exception as e:
        logger.error(f"检查contextToken失败: {e}")
        return False


def wait_for_user_message(timeout_minutes=30):
    """等待用户发送消息以刷新contextToken"""
    logger.info(f"等待用户发送消息（最多等待{timeout_minutes}分钟）...")

    start_time = time.time()
    end_time = start_time + timeout_minutes * 60

    while time.time() < end_time:
        try:
            # 检查是否有新消息
            cmd = 'openclaw cron list'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10, encoding='utf-8')

            # 再次检查contextToken
            if check_context_token():
                logger.info("contextToken已刷新")
                return True

            logger.info("等待用户发送消息...")
            time.sleep(30)  # 每30秒检查一次

        except Exception as e:
            logger.error(f"等待消息时出错: {e}")
            time.sleep(30)

    logger.warning("等待超时，用户未发送消息")
    return False


def send_news():
    """发送热点新闻"""
    logger.info("开始发送热点新闻...")

    # 检查contextToken是否有效
    if not check_context_token():
        logger.warning("contextToken无效，等待用户发送消息...")
        if not wait_for_user_message():
            logger.error("等待超时，无法发送热点新闻")
            return False

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

        # 分离知乎和GitHub新闻
        zhihu_news = [n for n in news_list if n.get("source") == "知乎热榜"][:5]
        github_news = [n for n in news_list if n.get("source") == "GitHub Trending"][:3]
        other_news = [n for n in news_list if n.get("source") not in ["知乎热榜", "GitHub Trending"]][:2]

        # 发送标题
        title_msg = f"📰 {today} 热点新闻速递"
        logger.info(f"发送标题: {title_msg}")
        cmd = f'openclaw message send --channel openclaw-weixin --target "o9cq80zOJNAxg1j5JcyFfH4KEzqk@im.wechat" --message "{title_msg}"'
        subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8')
        time.sleep(2)

        # 发送知乎热榜
        if zhihu_news:
            zhihu_msg = "🔥 知乎热榜"
            for i, news in enumerate(zhihu_news, 1):
                title = news.get("name", "")
                if len(title) > 35:
                    title = title[:35] + "..."
                zhihu_msg += f"\n{i}. {title}"

            logger.info(f"发送知乎热榜: {len(zhihu_news)}条")
            cmd = f'openclaw message send --channel openclaw-weixin --target "o9cq80zOJNAxg1j5JcyFfH4KEzqk@im.wechat" --message "{zhihu_msg}"'
            subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8')
            time.sleep(2)

        # 发送GitHub Trending
        if github_news:
            github_msg = "💻 GitHub Trending"
            for i, news in enumerate(github_news, 1):
                title = news.get("name", "")
                if len(title) > 35:
                    title = title[:35] + "..."
                github_msg += f"\n{i}. {title}"

            logger.info(f"发送GitHub Trending: {len(github_news)}条")
            cmd = f'openclaw message send --channel openclaw-weixin --target "o9cq80zOJNAxg1j5JcyFfH4KEzqk@im.wechat" --message "{github_msg}"'
            subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8')
            time.sleep(2)

        # 发送其他新闻
        if other_news:
            other_msg = "📌 其他热点"
            for i, news in enumerate(other_news, 1):
                title = news.get("name", "")
                if len(title) > 35:
                    title = title[:35] + "..."
                other_msg += f"\n{i}. {title}"

            logger.info(f"发送其他热点: {len(other_news)}条")
            cmd = f'openclaw message send --channel openclaw-weixin --target "o9cq80zOJNAxg1j5JcyFfH4KEzqk@im.wechat" --message "{other_msg}"'
            subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8')
            time.sleep(2)

        # 发送结尾
        end_msg = "————————————\n祝你今天愉快！😊"
        logger.info("发送结尾...")
        cmd = f'openclaw message send --channel openclaw-weixin --target "o9cq80zOJNAxg1j5JcyFfH4KEzqk@im.wechat" --message "{end_msg}"'
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
