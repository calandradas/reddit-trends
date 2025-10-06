#!/usr/bin/env python3
"""
Reddit Post Trend Report Generation

This script generates reports on trending posts from Reddit AI communities.
"""

import os
import sys
import logging
import argparse
import schedule
import time
import asyncio
from datetime import datetime, timedelta
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.reddit_collection.collector import RedditDataCollector
from services.llm_processing.report_processor import ReportProcessor
from database.mongodb import MongoDBClient
from config import REPORT_CONFIG, REDDIT_COMMUNITIES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("report_generation.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_report_directory_structure(base_dir: str = "reports", reference_date: Optional[datetime] = None) -> str:
    """
    Create a directory structure for reports based on year/month/day.
    
    Args:
        base_dir: Base directory for reports
        reference_date: Optional reference date to use (defaults to current date)
        
    Returns:
        Path to the created directory
    """
    # 使用参考日期或当前时间
    now = reference_date if reference_date is not None else datetime.now()
    year_dir = str(now.year)
    month_dir = f"{now.month:02d}"
    day_dir = f"{now.day:02d}"
    
    # Create the directory structure
    report_dir = os.path.join(base_dir, year_dir, month_dir, day_dir)
    os.makedirs(report_dir, exist_ok=True)
    
    logger.info(f"Created report directory: {report_dir}")
    return report_dir

def update_readme_with_latest_report(report_paths: Dict[str, str]) -> None:
    """
    Update both English and Chinese README files with links to the latest reports.
    
    Args:
        report_paths: Dictionary mapping language codes to report file paths
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    
    # Update English README
    update_english_readme(report_paths, date_str)
    
    # Update Chinese README
    update_chinese_readme(report_paths, date_str)
    
    logger.info(f"Updated README.md and README_CN.md with links to latest reports")

def update_english_readme(report_paths: Dict[str, str], date_str: str) -> None:
    """
    Update the English README.md with links to the latest reports.
    
    Args:
        report_paths: Dictionary mapping language codes to report file paths
        date_str: Current date string
    """
    readme_path = "README.md"
    
    # Read existing README to preserve language switcher
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Extract language switcher if it exists
            language_switcher = ""
            if "[English](README.md) | [中文](README_CN.md)" in content:
                language_switcher = "[English](README.md) | [中文](README_CN.md)\n\n"
    except FileNotFoundError:
        language_switcher = "[English](README.md) | [中文](README_CN.md)\n\n"
    
    # Create README content
    readme_content = f"# Reddit AI Trend Reports\n\n"
    readme_content += language_switcher
    readme_content += f"Automatically generate trend reports from AI-related Reddit communities, supporting both English and Chinese languages. Stay up-to-date with the latest developments in the AI field through daily reports.\n\n"
    readme_content += f"## Latest Reports ({date_str})\n\n"
    
    # 使用固定的latest_report链接，而不是实际文件路径
    readme_content += f"- [English Report](reports/latest_report_en.md)\n"
    readme_content += f"- [Chinese Report](reports/latest_report_zh.md)\n"
    
    # Read the rest of the original README
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            original_content = f.read()
            # Find the position after the "Latest Reports" section
            features_section_start = original_content.find("## Features")
            if features_section_start != -1:
                readme_content += "\n" + original_content[features_section_start:]
    except FileNotFoundError:
        # If README doesn't exist, add a basic about section
        readme_content += "\n## About\n\n"
        readme_content += "This repository contains daily reports on trending posts from Reddit AI communities.\n"
        readme_content += "Reports are generated automatically every day at 6:00 AM US Central Time.\n"
    
    # Write to README
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

def update_chinese_readme(report_paths: Dict[str, str], date_str: str) -> None:
    """
    Update the Chinese README_CN.md with links to the latest reports.
    
    Args:
        report_paths: Dictionary mapping language codes to report file paths
        date_str: Current date string
    """
    readme_path = "README_CN.md"
    
    # Read existing README to preserve language switcher
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Extract language switcher if it exists
            language_switcher = ""
            if "[English](README.md) | [中文](README_CN.md)" in content:
                language_switcher = "[English](README.md) | [中文](README_CN.md)\n\n"
    except FileNotFoundError:
        language_switcher = "[English](README.md) | [中文](README_CN.md)\n\n"
    
    # Create README content
    readme_content = f"# Reddit AI 趋势报告\n\n"
    readme_content += language_switcher
    readme_content += f"自动从Reddit AI相关社区生成趋势报告，支持英文和中文双语。通过每日报告，随时了解AI领域的最新发展。\n\n"
    readme_content += f"## 最新报告 ({date_str})\n\n"
    
    # 使用固定的latest_report链接，而不是实际文件路径
    readme_content += f"- [英文报告](reports/latest_report_en.md)\n"
    readme_content += f"- [中文报告](reports/latest_report_zh.md)\n"
    
    # Read the rest of the original README
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            original_content = f.read()
            # Find the position after the introduction
            features_section_start = original_content.find("## 功能特点")
            if features_section_start != -1:
                readme_content += "\n" + original_content[features_section_start:]
    except FileNotFoundError:
        # If README doesn't exist, add a basic about section
        readme_content += "\n## 关于\n\n"
        readme_content += "此仓库包含来自Reddit AI社区的每日趋势报告。\n"
        readme_content += "报告每天在美国中部时间早上6:00自动生成。\n"
    
    # Write to README
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

def generate_report(industry: str = "ai", languages: List[str] = None, skip_mongodb: bool = False,
                   reference_date: Optional[datetime] = None, 
                   hours: int = 24,
                   save_to_db: bool = True,
                   save_to_file: bool = True,
                   push_to_github: bool = False,
                   push_to_notion: bool = False,
                   push_telegrambot: bool = False) -> Dict[str, str]:
    """
    Generate a report on trending posts from Reddit AI communities.
    
    Args:
        languages: List of language codes to generate reports for
        skip_mongodb: Whether to skip saving the report to MongoDB
        reference_date: Optional specific date to generate report for (defaults to current time)
        hours: Number of hours to look back for posts
        save_to_db: Whether to save the report to MongoDB
        save_to_file: Whether to save the report to file
        push_to_github: Whether to push the report to GitHub
        
    Returns:
        Dictionary mapping language codes to report file paths
    """
    if languages is None:
        languages = REPORT_CONFIG.get('languages', ['en', 'zh'])
    
    logger.info(f"Starting report generation for languages: {languages}")
    start_time = time.time()
    
    # 使用参考日期或当前时间
    current_time = reference_date if reference_date is not None else datetime.now()
    logger.info(f"Using reference date: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize services
        reddit_collector = RedditDataCollector()
        report_processor = ReportProcessor()
         
        # Get subreddits from config
        subreddits = REDDIT_COMMUNITIES.get(f"{industry}_communities")
        posts_per_subreddit = REPORT_CONFIG.get('posts_per_subreddit', 100)
        
        # Collect data
        logger.info(f"Collecting data from {industry} subreddits: {subreddits}")

        # 计算时间范围 - 使用参考日期
        end_time = current_time
        start_time_range = end_time - timedelta(hours=hours)
        logger.info(f"Collecting posts from {start_time_range} to {end_time}")
        
        # 收集所有帖子
        all_posts = []
        for subreddit in subreddits:
            posts = reddit_collector.get_subreddit_posts(
                subreddit=subreddit,
                limit=posts_per_subreddit,
                time_filter="week"
            )
            # 根据参考时间过滤帖子
            filtered_by_time = []
            for post in posts:
                post_time = post.get('created_utc')
                if isinstance(post_time, str):
                    try:
                        post_time = datetime.fromisoformat(post_time.replace('Z', '+00:00'))
                    except ValueError:
                        continue
                if post_time and start_time_range <= post_time <= end_time:
                    filtered_by_time.append(post)
            
            all_posts.extend(filtered_by_time)
        
        # Filter posts with more than 10 comments
        filtered_posts = [post for post in all_posts if post.get('num_comments', 0) > 10]
        logger.info(f"Filtered {len(filtered_posts)} posts with more than 10 comments from {len(all_posts)} total posts")
        
        # Get weekly and monthly popular posts - 也需要根据参考日期调整
        weekly_posts = reddit_collector.get_weekly_popular_posts(subreddits)
        monthly_posts = reddit_collector.get_monthly_popular_posts(subreddits)
        
        # Get previous report data for comparison
        #previous_report = mongodb_client.get_latest_report()
        
        # Generate reports in multiple languages
        reports = report_processor.generate_multilingual_reports(
            filtered_posts, 
            None, 
            weekly_posts, 
            monthly_posts,
            languages,
            industry,
            save_to_file=save_to_file
        )
      
        # Create directory structure - 使用参考日期
        report_dir = create_report_directory_structure(reference_date=current_time)
        
        # Save reports to files
        report_paths = {}
        timestamp = current_time.strftime("%Y%m%d_%H%M%S")
        
        for lang, report in reports.items():
            # Create filename
            filename = f"report_{timestamp}_{industry}_{lang}.md"
            filepath = os.path.join(report_dir, filename)
            
            # Save report to file
            if save_to_file:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(report["content"])
            # Create symlink for latest report
            latest_path = os.path.join("reports", f"latest_report_{industry}_{lang}.md")
            if os.path.exists(latest_path):
                if os.path.islink(latest_path):
                    os.unlink(latest_path)
                else:
                    os.remove(latest_path)
            
            # Create relative path for symlink
            rel_path = os.path.relpath(filepath, os.path.dirname(latest_path))
            try:
                #os.symlink(rel_path, latest_path)
                shutil.copy2(filepath, latest_path)
                logger.info(f"Created symlink from {rel_path} to {latest_path}")
            except Exception as e:
                # On Windows, symlinks might not work without admin privileges
                logger.warning(f"Could not create symlink: {e}. Copying file instead.")
                shutil.copy2(filepath, latest_path)
            
            report_paths[lang] = filepath
            logger.info(f"Saved {lang} report to {filepath}")
        
        # Update README with links to latest reports
        #if save_to_file:
        #    update_readme_with_latest_report(report_paths)
        
        # Save report to MongoDB
        if save_to_db and not skip_mongodb:
            mongodb_client = MongoDBClient()
            mongodb_client.save_report(reports, filtered_posts, weekly_posts, monthly_posts)
            logger.info("Saved report to MongoDB")
        
        # 添加 GitHub 推送支持
        if push_to_github:
            try:
                from utils.github_integration import GitHubIntegration
                github_integration = GitHubIntegration()
                for lang, report_path in report_paths.items():
                    github_integration.commit_and_push_report(report_path)
                    github_integration.commit_and_push_report(os.path.join("reports", f"latest_report_{industry}_{lang}.md"))
                logger.info("Pushed report to GitHub")
            except ImportError:
                logger.warning("GitHub utils not found. Skipping GitHub push.")
            except Exception as e:
                logger.error(f"Error pushing to GitHub: {e}")

        # Notion publish report
        if push_to_notion:
            try:
                from utils.notion_publish import NotionPublisher
                note_publisher = NotionPublisher(overwrite=True)
                for lang, report in reports.items():
                    note_publisher.publish(md_content=report["content"],title=report["title"],date=report["timestamp"],language=lang,industry=industry)
                logger.info("Published report to Notion")
            except ImportError:
                logger.warning("Notion utils not found. Skipping Notion publish.")
            except Exception as e:
                logger.error(f"Error publishing to Notion: {e}")

        # Telegram sending report
        if push_telegrambot:
            try:
                from utils.telegram_bot import TelegramBot
                telegram_bot = TelegramBot()
                for lang, report in reports.items():
                    asyncio.run(telegram_bot.send_daily_report(report["content"]))
                logger.info("Sent reports via Telegram")
            except ImportError:
                logger.warning("Telegram bot utils not found. Skipping Telegram sending.")
            except Exception as e:
                logger.error(f"Error sending reports via Telegram: {e}")
        
        end_time = time.time()
        logger.info(f"Report generation completed in {end_time - start_time:.2f} seconds")
        
        return report_paths
    
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise

def schedule_report_generation(interval_hours: int = 24, skip_mongodb: bool = False) -> None:
    """
    Schedule report generation to run at specified intervals.
    
    Args:
        interval_hours: Interval in hours between report generation runs
        skip_mongodb: Whether to skip saving the report to MongoDB
    """
    # Get generation time from config
    generation_time = REPORT_CONFIG.get('generation_time', "06:00")
    
    # Schedule job
    logger.info(f"Scheduling report generation to run daily at {generation_time}")
    schedule.every().day.at(generation_time).do(lambda: generate_report(skip_mongodb=skip_mongodb))
    
    # Run immediately if interval is 0
    if interval_hours == 0:
        logger.info("Running report generation immediately")
        generate_report(skip_mongodb=skip_mongodb)
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def main():
    """
    主函数，处理命令行参数并运行报告生成
    """
    parser = argparse.ArgumentParser(description='生成Reddit 趋势报告')
    parser.add_argument('--languages', nargs='+', default=['en'], 
                        help='要生成报告的语言代码列表，例如：en zh')
    parser.add_argument('--skip-mongodb', action='store_true',
                        help='跳过保存报告到MongoDB')
    parser.add_argument("--industry", default="ai", help="Generate industry-specific reports, e.g., ai, biotech, crypto")
    args = parser.parse_args()
    
    # 设置日志
    #setup_logging()
    
    # 获取配置的语言列表
    languages = args.languages
    industry = args.industry
    
    try:
        # 初始化服务
        reddit_collector = RedditDataCollector()
        report_processor = ReportProcessor()
        
        # 收集数据
        logger.info("开始收集数据...")

        subreddits = REDDIT_COMMUNITIES.get(f"{industry}_communities")
        # 收集帖子数据
        posts_per_subreddit = REPORT_CONFIG.get('posts_per_subreddit', 10)
        
        # 收集所有帖子
        all_posts = []
        for subreddit in subreddits:
            posts = reddit_collector.get_subreddit_posts(
                subreddit=subreddit,
                limit=posts_per_subreddit,
                time_filter="week"
            )
            all_posts.extend(posts)
        
        # 过滤评论数大于10的帖子
        posts = [post for post in all_posts if post.get('num_comments', 0) > 10]
        
        # 收集每周和每月热门帖子
        weekly_popular_posts = reddit_collector.get_weekly_popular_posts(subreddits)
        monthly_popular_posts = reddit_collector.get_monthly_popular_posts(subreddits)
        
        # 生成报告
        logger.info(f"开始生成报告，语言: {languages}...")
        #report_paths = {}
        for lang in languages:
            report = report_processor.generate_report(
                posts, 
                weekly_popular_posts, 
                monthly_popular_posts,
                language=lang,
                industry=industry
            )
            
            # 保存报告到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 创建年/月/日目录结构
            current_date = datetime.now()
            year_dir = str(current_date.year)
            month_dir = f"{current_date.month:02d}"
            day_dir = f"{current_date.day:02d}"
            
            report_dir = os.path.join("reports", year_dir, month_dir, day_dir)
            os.makedirs(report_dir, exist_ok=True)

            report_filename = f"report_{timestamp}_{industry}_{lang}.md"
            report_path = os.path.join(report_dir, report_filename)
            
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report["content"])
            
            logger.info(f"报告已保存到: {report_path}")
            
            # 创建最新报告的符号链接
            latest_report_path = os.path.join("reports", f"latest_report_{industry}_{lang}.md")
            if os.path.exists(latest_report_path):
                    if os.path.islink(latest_report_path):
                        os.unlink(latest_report_path)
                    else:
                        os.remove(latest_report_path)
            
            # 创建符号链接（在Windows上可能需要管理员权限）
            rel_path = os.path.relpath(report_path, os.path.dirname(latest_report_path))
            try:
                os.symlink(rel_path, latest_report_path)
                logger.info(f"已创建最新报告的符号链接: {latest_report_path}")
            except OSError as e:
                # 如果无法创建符号链接，则复制文件
                logger.warning(f"无法创建符号链接，将复制文件: {e}")
                shutil.copy2(report_path, latest_report_path)
                logger.info(f"已复制最新报告到: {latest_report_path}")
            
            #report_paths[lang] = report_path
            
            # 保存到MongoDB（如果未指定跳过）
            if not args.skip_mongodb:
                try:
                    # 保存报告到MongoDB
                    mongo_client = MongoDBClient()
                    report_id = mongo_client.save_report(report, lang)
                    logger.info(f"报告已保存到MongoDB，ID: {report_id}")
                except Exception as e:
                    logger.error(f"保存报告到MongoDB失败: {e}")
            else:
                logger.info("已跳过保存报告到MongoDB")
        
        # 更新README文件
        #update_readme_with_latest_report(report_paths)
        
        logger.info("报告生成完成")
        return True
    except Exception as e:
        logger.exception(f"报告生成失败: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate reports on trending posts from Reddit AI communities")
    parser.add_argument("--interval", type=int, default=24, help="Interval in hours between report generation runs")
    parser.add_argument("--languages", nargs="+", default=None, help="Languages to generate reports for (e.g., en zh)")
    parser.add_argument("--skip-mongodb", action="store_true", help="Skip saving reports to MongoDB")
    parser.add_argument("--push-to-github", action="store_true", help="Enable pushing reports to GitHub")
    parser.add_argument("--push-telegrambot", action="store_true", help="Enable sending reports via Telegram bot")
    parser.add_argument("--push-to-notion", action="store_true", help="Enable sending reports to Notion")
    parser.add_argument("--industry", default="ai", help="Generate industry-specific reports, e.g., ai, biotech, crypto")

    args = parser.parse_args()
    
    #main()
    if args.languages:
     # Run once with specified languages
         generate_report(args.industry, args.languages, skip_mongodb=args.skip_mongodb, push_telegrambot=args.push_telegrambot, push_to_github=args.push_to_github, push_to_notion=args.push_to_notion)
    #else:
        # Schedule with default languages from config
