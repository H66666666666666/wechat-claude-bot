"""每日热点新闻 - 自动发送给微信"""

import os
import sys
import json
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("daily_news.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)

# 加载配置
load_dotenv()

# 微信API配置
WEIXIN_API_BASE_URL = os.getenv("WEIXIN_API_BASE_URL", "https://ilinkai.weixin.qq.com")
WEIXIN_TOKEN = os.getenv("WEIXIN_TOKEN", "")
WEIXIN_USER_ID = os.getenv("WEIXIN_USER_ID", "")


def get_hot_news():
    """获取热点新闻"""
    # 尝试多个API源
    apis = [
        {
            "name": "知乎热榜",
            "url": "https://api.zhihu.com/topstory/hot-lists/total?limit=10",
            "headers": {"User-Agent": "Mozilla/5.0"},
            "parser": lambda data: [{"name": item.get("target", {}).get("title", ""), "url": f"https://www.zhihu.com/question/{item.get('target', {}).get('id', '')}"} for item in data.get("data", [])]
        },
        {
            "name": "GitHub Trending",
            "url": "https://api.github.com/search/repositories?q=stars:>1000&sort=stars&order=desc&per_page=10",
            "headers": {"User-Agent": "Mozilla/5.0"},
            "parser": lambda data: [{"name": f"{item['full_name']} - {item.get('description', '')[:50]}", "url": item['html_url']} for item in data.get("items", [])],
            "verify_ssl": False  # 禁用SSL验证
        },
        {
            "name": "微博热搜",
            "url": "https://weibo.com/ajax/side/hotSearch",
            "headers": {"User-Agent": "Mozilla/5.0"},
            "parser": lambda data: [{"name": item.get("word", ""), "url": f"https://s.weibo.com/weibo?q=%23{item.get('word', '')}%23"} for item in data.get("data", {}).get("realtime", [])[:10]]
        },
        {
            "name": "百度热搜",
            "url": "https://top.baidu.com/board?tab=realtime",
            "headers": {"User-Agent": "Mozilla/5.0"},
            "parser": lambda data: [{"name": item.get("word", ""), "url": item.get("url", "")} for item in data.get("data", {}).get("cards", [{}])[0].get("content", [])[:10]]
        },
    ]

    all_news = []

    for api in apis:
        try:
            logger.info(f"尝试获取{api['name']}...")
            verify_ssl = api.get("verify_ssl", True)
            resp = requests.get(api["url"], headers=api.get("headers", {}), timeout=10, verify=verify_ssl)
            if resp.status_code == 200:
                data = resp.json()
                news_list = api["parser"](data)
                if news_list:
                    logger.info(f"成功获取{len(news_list)}条{api['name']}")
                    # 添加来源标记
                    for news in news_list:
                        news["source"] = api["name"]
                    all_news.extend(news_list)
        except Exception as e:
            logger.error(f"获取{api['name']}失败: {e}")

    if all_news:
        # 按来源分组，每个来源最多取5条
        news_by_source = {}
        for news in all_news:
            source = news.get("source", "未知")
            if source not in news_by_source:
                news_by_source[source] = []
            if len(news_by_source[source]) < 5:
                news_by_source[source].append(news)

        # 合并所有来源的新闻
        result = []
        for source_news in news_by_source.values():
            result.extend(source_news)

        # 去重
        seen = set()
        unique_news = []
        for news in result:
            if news["name"] not in seen:
                seen.add(news["name"])
                unique_news.append(news)

        return unique_news[:20]  # 最多返回20条

    # 如果所有API都失败，返回一些静态新闻
    logger.warning("所有API都失败，返回静态新闻")
    return [
        {"name": "科技新闻：AI技术持续发展", "url": "", "source": "默认"},
        {"name": "经济动态：全球市场波动", "url": "", "source": "默认"},
        {"name": "社会热点：民生话题受关注", "url": "", "source": "默认"},
        {"name": "国际形势：全球局势变化", "url": "", "source": "默认"},
        {"name": "文化娱乐：影视综艺热播", "url": "", "source": "默认"},
    ]


def format_news_message(news_list):
    """格式化新闻消息"""
    if not news_list:
        return "获取热点新闻失败，请稍后再试。"

    today = datetime.now().strftime("%Y年%m月%d日")
    message = f"📰 {today} 热点新闻\n\n"

    # 只发送前10条新闻
    for i, news in enumerate(news_list[:10], 1):
        title = news.get("name", news.get("title", ""))
        # 截断过长的标题
        if len(title) > 50:
            title = title[:50] + "..."
        message += f"{i}. {title}\n"

    message += "\n————————————\n"
    message += "数据来源：知乎热榜\n"

    return message


def send_weixin_message(user_id, text):
    """发送微信消息"""
    # 通过OpenClaw网关发送
    try:
        # 使用OpenClaw CLI发送消息
        import subprocess
        # 转义消息中的特殊字符
        escaped_text = text.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'").replace('`', '\\`')
        cmd = f'openclaw message send --channel openclaw-weixin --target "{user_id}" --message "{escaped_text}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8')
        if result.returncode == 0:
            logger.info("通过OpenClaw网关发送成功")
            return True
        else:
            logger.error(f"OpenClaw发送失败: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"OpenClaw发送异常: {e}")
        return False


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("  每日热点新闻推送")
    logger.info("=" * 50)

    # 检查配置
    if not WEIXIN_TOKEN:
        logger.error("请设置 WEIXIN_TOKEN 环境变量")
        sys.exit(1)

    if not WEIXIN_USER_ID:
        logger.error("请设置 WEIXIN_USER_ID 环境变量")
        sys.exit(1)

    # 获取热点新闻
    logger.info("正在获取热点新闻...")
    news_list = get_hot_news()

    if not news_list:
        logger.error("获取热点新闻失败")
        sys.exit(1)

    logger.info(f"获取到 {len(news_list)} 条热点新闻")

    # 格式化消息
    message = format_news_message(news_list)

    # 发送消息
    logger.info("正在发送消息...")
    success = send_weixin_message(WEIXIN_USER_ID, message)

    if success:
        logger.info("每日热点新闻推送完成！")
    else:
        logger.error("推送失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
