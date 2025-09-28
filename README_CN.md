# Reddit 产业 趋势报告

[English](README.md) | [中文](README_CN.md)

从 liyedanpdx/reddit-ai-trends fork而来, 感谢他的分享。

本分支增加对OpenAI, xAI Grok, and Google Gemini的支持。具体参考.env.example文件的配置信息。

自动从Reddit AI, Crypto, Biotech相关社区生成趋势报告，支持英文和中文双语。

自定义你所关心的产业社区，并生成报告。

通过每日报告，随时了解AI, Crypto, Biotech领域的最新发展。

## 功能特点

- **实时趋势监控**：实时跟踪新兴产业技术、讨论和突破性进展
- **多个LLM支持**：增加对OpenAI, xAI Grok, and Google Gemini的支持
- **多产业分析，自定义**：增加对AI、Biotech、Crypto产业社区的支持，可自定义添加多个产业
- **分别生成产业报告**: 按产业生产报告，可定义多个计划任务
- **多社区分析**：收集来自各种相关产业subreddit的数据，提供全面视图
- **详细趋势分析**：生成深入报告，包括今日焦点、周趋势对比、月度技术演进等
- **双语支持**：同时生成英文和中文报告
- **有组织的文件结构**：按年/月/日存储报告，便于访问
- **Docker部署**：简易容器化部署
- **MongoDB持久化**：存储所有数据用于历史分析

## 目录结构

```
reports/
  ├── YYYY/           # 年份目录
  │   ├── MM/         # 月份目录
  │   │   ├── DD/     # 日期目录
  │   │   │   ├── report_YYYYMMDD_HHMMSS_industry_en.md  # 英文报告
  │   │   │   └── report_YYYYMMDD_HHMMSS_industry_zh.md  # 中文报告
  ├── latest_report_industry_en.md  # 最新英文报告的符号链接
  └── latest_report_industry_zh.md  # 最新中文报告的符号链接
```

## 安装与设置

### 前提条件

- Docker和Docker Compose
- Reddit API凭证
- LLM API key, OpenAI | Google Gemini | xAI Grok 密钥

### 环境变量设置

1. 复制`.env.example`文件为`.env`：

```bash
cp .env.example .env
```

2. 编辑`.env`文件，填入您的API密钥和其他配置：选择LLM Vendor, 并配置相应的key

```
# Reddit API credentials
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_reddit_user_agent

#LLM Vendor
VENDOR=gemini
#VENDOR=grok
#VENDOR=openai

#gemini api key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash # You can change to gemini-2.5-flash, gemini-3, etc.

#grok api key
GROK_API_KEY=your_grok_api_key
GROK_API_BASE=https://api.grok.com/v1_
GROK_MODEL=grok-4 # You can change to grok-4, grok-5, etc.

# OpenAI API key
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o # You can change to gpt-4.1, gpt-4o, gpt-5-mini, etc.

```

Reddit API credentials website: [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)

Google gemini API website: [https://aistudio.google.com/app/api-keys](https://aistudio.google.com/app/api-keys)

xAI grok API website: [https://x.ai/api](https://x.ai/api)

OpenAI API website: [https://platform.openai.com/](https://platform.openai.com/)

## 使用方法

### 使用Docker Compose部署

1. 构建并启动容器：

```bash
docker-compose up -d
```

2. 查看日志：

```bash
docker-compose logs -f app
```

### 手动运行

1. 安装依赖：

```bash
python3 -m venv reddit-trends
cd reddit-trends
source ./bin/activate
pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
pip install -r requirements.txt
```

2. 生成一次性报告：

```bash
python report_generation.py --languages en zh --skip-mongodb --industry ai
```

3. 设置定时生成报告：

```bash
crontab -e

# m h  dom mon dow   command
0 7 * * * /path/to/reddit-trends/report_generation.sh ai
0 8 * * * /path/to/reddit-trends/report_generation.sh crypto
0 9 * * * /path/to/reddit-trends/report_generation.sh biotech
```


## 创建GitHub仓库

1. 在GitHub上创建一个新仓库

2. 初始化本地仓库并推送：

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/reddit-ai-trends.git
git push -u origin main
```

## 自定义配置

您可以在`config.py`文件中修改以下配置：

- 要监控的subreddit列表，可添加多个产业
- 每个subreddit要获取的帖子数量
- 报告生成时间
- 支持的语言
- LLM模型参数

## 添加新的产业社区方法

- 编辑`config.py`文件中的`REDDIT_COMMUNITIES`参数内容
- 在`REDDIT_COMMUNITIES`开头添加要监测的产业社区，例如

```py
    "biotech_communities": [
        "Biotech",
        "Bioinformatics",
        "medicine",
        "biology"
    ],
```

在运行脚本时，添加`--industry`相对的参数即可，注意参数名与添加的产业社区前缀必须保持一致

```bash
python report_generation.py --languages en zh --skip-mongodb --industry biotech
```

## 多产业趋势监控

该系统旨在通过以下方式让您了解相关产业领域的最新发展：

- 实时跟踪新兴技术和突破性进展
- 识别不同AI社区的热门话题
- 将当前趋势与历史数据比较以发现新兴模式
- 突出小型社区中可能被忽视的独特讨论
- 对特别有趣或重要的趋势提供技术深度分析

每日报告为您提供多个产业世界正在发生的事情的全面视图，帮助您保持领先地位并在它们出现时识别重要发展。

## 故障排除

- **报告未生成**：检查API密钥是否正确，以及日志中是否有错误信息
- **MongoDB连接失败**：确保MongoDB服务正在运行，并且连接URI正确
- **符号链接不工作**：在Windows系统上，可能需要管理员权限来创建符号链接

## 许可证

MIT 