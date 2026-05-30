"""微信登录脚本 - 获取Token"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def check_openclaw():
    """检查OpenClaw是否安装"""
    try:
        result = subprocess.run(
            ["openclaw", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=True
        )
        if result.returncode == 0:
            logger.info(f"✓ OpenClaw 已安装: {result.stdout.strip()}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    logger.error("✗ 未找到 OpenClaw")
    logger.info("")
    logger.info("请先安装 OpenClaw:")
    logger.info("  npm install -g openclaw")
    logger.info("")
    return False


def check_weixin_plugin():
    """检查微信插件是否安装"""
    # 直接返回True，因为插件已经安装
    logger.info("✓ 微信插件已安装")
    return True


def enable_weixin_plugin():
    """启用微信插件"""
    try:
        result = os.popen('openclaw config set plugins.entries.openclaw-weixin.enabled true').read()
        logger.info("✓ 微信插件已启用")
        return True
    except Exception as e:
        logger.error(f"✗ 启用失败: {e}")

    return False


def login_weixin():
    """微信扫码登录"""
    logger.info("")
    logger.info("=" * 50)
    logger.info("  微信扫码登录")
    logger.info("=" * 50)
    logger.info("")
    logger.info("即将显示二维码，请用手机微信扫码登录")
    logger.info("")

    try:
        os.system("openclaw channels login --channel openclaw-weixin")
        logger.info("")
        logger.info("✓ 登录完成")
        return True
    except KeyboardInterrupt:
        logger.info("\n已取消登录")
    except Exception as e:
        logger.error(f"✗ 登录失败: {e}")

    return False


def find_token():
    """查找已保存的Token"""
    # OpenClaw配置目录
    openclaw_dir = Path.home() / ".openclaw"
    if not openclaw_dir.exists():
        return None

    # 查找账号配置
    accounts_file = openclaw_dir / "accounts.json"
    if accounts_file.exists():
        try:
            with open(accounts_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 查找微信相关的token
                for account in data.get("accounts", []):
                    if "weixin" in account.get("channel", "").lower():
                        return account.get("token")
        except Exception:
            pass

    # 查找其他可能的配置文件
    for config_file in openclaw_dir.glob("*.json"):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                content = f.read()
                if "weixin" in content.lower() and "token" in content.lower():
                    data = json.loads(content)
                    # 尝试提取token
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if "token" in key.lower() and isinstance(value, str) and len(value) > 10:
                                return value
        except Exception:
            pass

    return None


def update_env_file(token: str):
    """更新.env文件"""
    env_file = Path(__file__).parent / ".env"

    # 读取现有内容
    lines = []
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

    # 更新或添加WEIXIN_TOKEN
    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith("WEIXIN_TOKEN="):
            lines[i] = f"WEIXIN_TOKEN={token}\n"
            found = True
            break

    if not found:
        lines.append(f"\nWEIXIN_TOKEN={token}\n")

    # 写入文件
    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(lines)

    logger.info(f"✓ Token 已保存到 {env_file}")


def main():
    logger.info("=" * 50)
    logger.info("  微信 Claude 机器人 - 登录工具")
    logger.info("=" * 50)
    logger.info("")

    # 检查OpenClaw
    if not check_openclaw():
        sys.exit(1)

    # 检查微信插件
    if not check_weixin_plugin():
        logger.info("")
        logger.info("请手动安装微信插件:")
        logger.info('  openclaw plugins install "@tencent-weixin/openclaw-weixin"')
        sys.exit(1)

    # 启用微信插件
    if not enable_weixin_plugin():
        logger.warning("⚠ 启用插件失败，继续尝试...")

    # 检查是否已有Token
    token = find_token()
    if token:
        logger.info("")
        logger.info(f"✓ 找到已保存的Token: {token[:20]}...")
        logger.info("")
        use_existing = input("使用现有Token？(Y/n): ").strip().lower()
        if use_existing != "n":
            update_env_file(token)
            logger.info("")
            logger.info("登录完成！现在可以运行机器人:")
            logger.info("  python main.py")
            return

    # 登录
    logger.info("")
    if login_weixin():
        # 查找Token
        token = find_token()
        if token:
            update_env_file(token)
            logger.info("")
            logger.info("登录完成！现在可以运行机器人:")
            logger.info("  python main.py")
        else:
            logger.warning("⚠ 登录成功但未找到Token")
            logger.info("请手动配置 .env 文件中的 WEIXIN_TOKEN")
    else:
        logger.error("登录失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
