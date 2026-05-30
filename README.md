# 微信 Claude 机器人

基于 OpenClaw + openclaw-weixin 插件的微信 AI 机器人，支持 Claude/MiMo API，可定时推送热点新闻。

## ✨ 功能特性

- 🤖 **AI 对话**：基于 Claude/MiMo API 的智能对话
- 📰 **热点新闻**：每日自动推送热点新闻（知乎热榜）
- ⏰ **定时任务**：支持定时发送消息
- 🚀 **开机自启**：开机登录后自动发送新闻
- 💬 **多轮对话**：支持上下文记忆的多轮对话
- 🔧 **命令控制**：支持 /clear、/help 等命令

## 📋 前提条件

1. 已安装 [OpenClaw](https://docs.openclaw.ai/install)
2. 已安装并启用 `@tencent-weixin/openclaw-weixin` 插件
3. 已完成微信扫码登录授权
4. 有 Claude/MiMo API Key

## 🚀 快速开始

### 1. 安装依赖

```bash
cd wechat-claude-bot
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

### 3. 配置 OpenClaw

```bash
# 安装 OpenClaw
npm install -g openclaw

# 安装微信插件
openclaw plugins install "@tencent-weixin/openclaw-weixin"

# 启用插件
openclaw config set plugins.entries.openclaw-weixin.enabled true

# 扫码登录
openclaw channels login --channel openclaw-weixin

# 启动网关
openclaw gateway start
```

### 4. 运行机器人

```bash
python main.py
```

## 📁 项目结构

```
wechat-claude-bot/
├── main.py              # 主程序（AI 对话）
├── weixin_api.py        # 微信 API 客户端
├── claude_api.py        # Claude/MiMo API 客户端
├── daily_news.py        # 每日热点新闻推送
├── startup_news.py      # 开机自启动发送新闻
├── login.py             # 微信登录工具
├── test_claude.py       # API 测试脚本
├── config.py            # 配置管理
├── requirements.txt     # 依赖列表
├── .env.example         # 配置示例
├── start.bat            # Windows 启动脚本
└── setup_daily_news.bat # 设置每日新闻计划任务
```

## ⚙️ 配置说明

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `WEIXIN_API_BASE_URL` | 微信 API 地址 | `https://ilinkai.weixin.qq.com` |
| `WEIXIN_TOKEN` | 微信 Token | - |
| `WEIXIN_USER_ID` | 接收消息的用户 ID | - |
| `CLAUDE_API_KEY` | Claude/MiMo API Key | - |
| `CLAUDE_MODEL` | 模型名称 | `mimo-v2-pro` |
| `CLAUDE_MAX_TOKENS` | 最大回复长度 | `4096` |
| `SYSTEM_PROMPT` | 系统提示词 | 默认中文助手 |

## 📰 每日热点新闻

### 手动发送

```bash
python daily_news.py
```

### 设置定时任务

```bash
# 方式 1：使用 OpenClaw cron（推荐）
openclaw cron add --name "daily-news" --cron "0 8 * * *" \
  --channel openclaw-weixin \
  --to "你的用户ID" \
  --message "请发送今日热点新闻" \
  --announce

# 方式 2：使用 Windows 计划任务
setup_daily_news.bat
```

### 开机自启动

```bash
# 创建 Windows 计划任务
schtasks /Create /TN "StartupNews" /TR "python D:\path\to\startup_news.py" /SC ONLOGON /DELAY 0000:30 /F
```

## 🤖 命令列表

| 命令 | 说明 |
|------|------|
| `/clear` 或 `清除记录` | 清除对话历史 |
| `/help` 或 `帮助` | 显示帮助信息 |

## 🔧 常见问题

### Q: 如何获取微信 Token？

A: 通过 OpenClaw 的 `openclaw channels login --channel openclaw-weixin` 命令扫码登录后，Token 会自动保存。

### Q: 为什么收不到消息？

A: 可能原因：
1. OpenClaw 网关未启动
2. 微信 Token 过期
3. 网络问题

### Q: 如何修改新闻推送时间？

A: 修改 OpenClaw cron 任务的 cron 表达式，例如：
- 每天早上 8 点：`0 8 * * *`
- 每天晚上 10 点：`0 22 * * *`

### Q: 支持哪些 AI 模型？

A: 支持所有 OpenAI 兼容的 API，包括：
- Claude (Anthropic)
- MiMo (小米)
- GPT (OpenAI)
- 其他兼容 API

## 📝 更新日志

### v1.0.0 (2026-05-30)
- ✨ 初始版本
- 🤖 支持 AI 对话
- 📰 支持每日热点新闻推送
- ⏰ 支持定时任务
- 🚀 支持开机自启动

## 📄 许可证

MIT License

## 🙏 致谢

- [OpenClaw](https://github.com/anthropics/openclaw) - AI Agent 框架
- [openclaw-weixin](https://github.com/nicepkg/openclaw-weixin) - 微信渠道插件
- [MiMo](https://github.com/XiaoMi/MiMo) - 小米 AI 模型
