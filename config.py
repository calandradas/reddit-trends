"""
Configuration file for Reddit Post Trend Analyzer
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Reddit communities to monitor
REDDIT_COMMUNITIES = {
    "ai_communities": [
        "LocalLLaMA",
        "MachineLearning",
        "singularity",
        "LocalLLM",
        "hackernews",
        "LangChain",
        "LLMDevs",
        "Vectordatabase",
        "Rag",
        "ai_agents",
        "embedded",
        "technology",
        "datascience"
    ],

    "biotech_communities": [
        "Biotech",
        "Bioinformatics",
        "medicine",
        "biology",
        "genetics",
        "neuroscience",
        "Pharmacology",
        "HealthInformatics",
        "MedTech",
        "science",
        "CRISPR"
    ],

    "crypto_communities": [
        "CryptoCurrency",
        "Bitcoin",
        "ethereum",
        "fintech",
        "financialtechnology",
        "DeFi",
        "CryptoMarkets",
        "personalfinance",
        "investing",
        "Altcoin",
        "CryptoTechnology",
        "finance",
        "FinancialPlanning",
        "WallStreetBets",
        "stocks",
        "options",
        "Economics",
        "dividends"
    ],

    "geopolitical_communities": [
        "geopolitics",
        "worldnews",
        "internationalpolitics",
        "Economics",
        "PoliticalDiscussion",
        "ForeignAffairs",
        "IRstudies",
        "globalpolitics",
        "AskEconomics",
        "finance",
        "investing",
        "worldevents"
    ]
}

# LLM configuration
LLM_CONFIG = {
    "temperature": 0.4,
    "max_tokens": 12000
}

# Report generation configuration
REPORT_CONFIG = {
    "frequency_hours": 24,  # 更新为每24小时一次
    "report_title_format": "Reddit Trends Report - {date}",
    "report_title_format_zh": "Reddit 趋势报告 - {date}",
    "report_directory": "reports",
    "database_name": "reddit-report",
    "collections": {
        "posts": "posts",
        "reports": "reports"
    },
    # 从环境变量加载报告生成时间，默认为美国中部时间早上6点
    "generation_time": os.getenv("REPORT_GENERATION_TIME", "06:00"),
    # 支持的语言列表，默认为英文和中文
    "languages": os.getenv("REPORT_LANGUAGES", "en,zh").split(","),
    # 每个subreddit获取的帖子数量
    "posts_per_subreddit": 30
}

# Post categories
POST_CATEGORIES = [
    "Technical Problem",
    "Technical Solution",
    "New Technology",
    "Large Language Model",
    "Application",
    "Best Practice",
    "Research",
    "Discussion",
    "News",
    "Other"
]

# 从环境变量加载要排除的类别
EXCLUDED_CATEGORIES = os.getenv("EXCLUDED_CATEGORIES", "").split(",")
# 移除空字符串
EXCLUDED_CATEGORIES = [cat.strip() for cat in EXCLUDED_CATEGORIES if cat.strip()]

# GitHub configuration
GITHUB_CONFIG = {
    "repo_name": "reddit-trends",
    "branch": "main",
    "commit_message_format": "Update report for {date}"
}

# Docker configuration
DOCKER_CONFIG = {
    "image_name": "reddit-trends-report",
    "container_name": "reddit-trends-report-container",
    "port": 8080
} 
