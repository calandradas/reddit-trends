"""
LLM API Client

This module provides functionality to interact with the LLM API for processing.
"""

import os
import logging
from datetime import datetime, timedelta
import groq
from google import genai
from google.genai import types
from openai import OpenAI
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from config import LLM_CONFIG
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMClient:
    """Client for interacting with the LLM API."""
    
    def __init__(self):
        """Initialize the LLM API client using credentials from environment variables."""
        self.vendor = os.getenv('VENDOR', 'gemini')  # Default to 'gemini' if not set
        match self.vendor:
            case 'grok':
                self.api_key = os.getenv('GROK_API_KEY')
                self.api_base = os.getenv('GROK_API_BASE')
                self.client = OpenAI(api_key=self.api_key, api_base=self.api_base)
                self.model = os.getenv('GROK_MODEL', "grok-4")
            case 'openai':
                self.api_key = os.getenv('OPENAI_API_KEY')
                self.client = OpenAI(api_key=self.api_key)
                self.model = os.getenv('OPENAI_MODEL', "gpt-4o")
            case 'gemini':
                self.api_key = os.getenv('GEMINI_API_KEY')
                self.client = genai.Client(api_key=self.api_key)
                self.model = os.getenv('GEMINI_MODEL', "gemini-2.5-flash")
            case _:
                raise ValueError("LLM Vendor and API key not found in environment variables")
        
        self.temperature = LLM_CONFIG['temperature']
        self.max_tokens = LLM_CONFIG['max_tokens']
        
        logger.info(f"LLM API client initialized with model: {self.model}")
    
    def generate_text(self, 
                     prompt: str, 
                     temperature: Optional[float] = None, 
                     max_tokens: Optional[int] = None) -> str:
        """
        Generate text using the Groq API.
        
        Args:
            prompt: The prompt to send to the model
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            
        Returns:
            Generated text
        """
        # Use provided parameters or defaults
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        logger.info(f"Generating text with model: {self.model}, temperature: {temp}, max_tokens: {tokens}")
        
        try:
            match self.vendor:
                case 'grok' | 'openai':
                # Call the grok & chatgpt API
                    response = self.client.chat.completions.create(              
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that provides accurate and factual information."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=temp,
                        max_tokens=tokens
                    ) 
                                
                    # Extract the generated text groq & chatgpt api
                    generated_text = response.choices[0].message.content
                case 'gemini':  
                    # call gemini api
                            # 使用 system_instruction 来创建配置，用于设定模型的初始行为
                    config = types.GenerateContentConfig(
                        system_instruction=" You are a helpful assistant that provides accurate and factual information."
                    )

                    # 创建聊天会话
                    self.chat_session = self.client.chats.create(
                        model=self.model,
                        config=config # 传递系统指令配置
                    )

                    # 1. 创建 GenerationConfig 对象来设置参数
                    generation_config = types.GenerateContentConfig(
                        temperature=temp,
                        max_output_tokens=tokens
                    )
                    
                    # 2. 调用 send_message，并传入配置
                    response = self.chat_session.send_message(
                        message=prompt,
                        config=generation_config
                    )

                    # gemini api
                    generated_text = response.text
                    #end gemini api
            
            # Remove <think></think> tags and their content using regex
            generated_text = re.sub(r'<think>.*?</think>', '', generated_text, flags=re.DOTALL)
            
            logger.info(f"Successfully generated text ({len(generated_text)} chars)")
            return generated_text
        
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise
    
    def analyze_posts(self, posts: List[Dict[str, Any]]) -> str:
        """
        Analyze a list of Reddit posts and generate insights.
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Analysis text
        """
        if not posts:
            return "No posts to analyze."
        
        # Create a summary of the posts
        post_summaries = []
        for i, post in enumerate(posts[:20], 1):  # Limit to 20 posts to avoid token limits
            summary = (
                f"{i}. Title: {post.get('title', 'No title')}\n"
                f"   Subreddit: r/{post.get('subreddit', 'unknown')}\n"
                f"   Score: {post.get('score', 0)}, Comments: {post.get('num_comments', 0)}\n"
                f"   Category: {post.get('category', 'Other')}\n"
                f"   URL: {post.get('permalink', 'No URL')}\n"
                f"   Content: {post.get('selftext', '')[:200]}{'...' if len(post.get('selftext', '')) > 200 else ''}\n"
            )
            post_summaries.append(summary)
        
        post_summary_text = "\n".join(post_summaries)
        
        # Create the prompt
        prompt = f"""
        You are an AI assistant tasked with analyzing recent trending posts from Reddit AI and technology communities.
        
        Below are summaries of {len(posts)} recent posts:
        
        {post_summary_text}
        
        Please provide a comprehensive analysis of these posts, including:
        
        1. Key Trends: Identify 3-5 major trends or themes emerging from these posts.
        2. Notable Discussions: Highlight the most significant discussions or debates.
        3. New Technologies: Identify any new technologies, tools, or models mentioned.
        4. Community Interests: What topics seem to be generating the most interest?
        5. Technical Insights: Extract valuable technical insights or solutions shared.
        
        Format your response as a well-structured report with clear sections and bullet points where appropriate.
        Focus on being factual, concise, and informative. Avoid speculation and stick to what's evident from the posts.
        """
        
        # Generate the analysis
        return self.generate_text(prompt)
    
    def _create_monthly_popular_table(self, posts: List[Dict[str, Any]], previous_report: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a markdown table of popular posts from the last month.
        
        Args:
            posts: List of post dictionaries
            previous_report: Optional dictionary containing previous report data for comparison
            
        Returns:
            Markdown table as a string
        """
        # Sort posts by score (descending)
        sorted_posts = sorted(posts, key=lambda x: x.get('score', 0), reverse=True)
        
        # Take top 20 posts
        top_posts = sorted_posts[:20]
        
        # Create table header
        table = "## Monthly Popular Posts\n\n"
        table += "| # | Title | Community | Score | Comments | Category | Posted |\n"
        table += "|---|-------|-----------|-------|----------|----------|--------|\n"
        
        # Add rows to table
        for i, post in enumerate(top_posts, 1):
            title = post.get('title', 'N/A')
            
            # Enhanced title processing to prevent Markdown formatting issues
            # 1. Replace pipe characters that would break table formatting
            title = title.replace('|', '&#124;')
            
            # 2. Escape all brackets to prevent Markdown link interpretation
            title = title.replace('[', '\\[').replace(']', '\\]')
            
            # 3. Escape quotes to prevent string interpretation issues
            title = title.replace('"', '\\"').replace("'", "\\'")
            
            # 4. Replace any newline characters or carriage returns that might be in the title
            title = title.replace('\n', ' ').replace('\r', ' ')
            
            # 5. Replace periods followed by spaces with periods and non-breaking spaces
            # to prevent line breaks after periods
            title = title.replace('. ', '.&nbsp;')
            
            # Truncate long titles
            if len(title) > 60:
                title = title[:57] + "..."
            
            # Get community (subreddit) information
            subreddit = post.get('subreddit', 'N/A')
            subreddit_url = f"https://www.reddit.com/r/{subreddit}"
            community_link = f"[r/{subreddit}]({subreddit_url})"
            
            score = post.get('score', 0)
            comments = post.get('num_comments', 0)
            category = post.get('link_flair_text', 'N/A')
            if not category or category == 'None':
                category = 'General'
            
            # Format the timestamp
            created_utc = post.get('created_utc')
            if created_utc:
                if isinstance(created_utc, str):
                    try:
                        created_utc = datetime.fromisoformat(created_utc.replace('Z', '+00:00'))
                    except ValueError:
                        created_utc = datetime.utcnow()
                posted_time = created_utc.strftime("%Y-%m-%d %H:%M UTC")
            else:
                posted_time = 'N/A'
            
            # Create post URL
            post_id = post.get('post_id', '')
            post_url = f"https://www.reddit.com/comments/{post_id}"
            
            # Add row to table
            table += f"| {i} | [{title}]({post_url}) | {community_link} | {score} | {comments} | {category} | {posted_time} |\n"
        
        return table
    
    def _create_weekly_popular_table(self, posts: List[Dict[str, Any]], previous_report: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a markdown table of popular posts from the last week.
        
        Args:
            posts: List of post dictionaries
            previous_report: Optional dictionary containing previous report data for comparison
            
        Returns:
            Markdown table as a string
        """
        # Sort posts by score (descending)
        sorted_posts = sorted(posts, key=lambda x: x.get('score', 0), reverse=True)
        
        # Take top 20 posts
        top_posts = sorted_posts[:20]
        
        # Create table header
        table = "## Weekly Popular Posts\n\n"
        table += "| # | Title | Community | Score | Comments | Category | Posted |\n"
        table += "|---|-------|-----------|-------|----------|----------|--------|\n"
        
        # Add rows to table
        for i, post in enumerate(top_posts, 1):
            title = post.get('title', 'N/A')
            
            # Enhanced title processing to prevent Markdown formatting issues
            # 1. Replace pipe characters that would break table formatting
            title = title.replace('|', '&#124;')
            
            # 2. Escape all brackets to prevent Markdown link interpretation
            title = title.replace('[', '\\[').replace(']', '\\]')
            
            # 3. Escape quotes to prevent string interpretation issues
            title = title.replace('"', '\\"').replace("'", "\\'")
            
            # 4. Replace any newline characters or carriage returns that might be in the title
            title = title.replace('\n', ' ').replace('\r', ' ')
            
            # 5. Replace periods followed by spaces with periods and non-breaking spaces
            # to prevent line breaks after periods
            title = title.replace('. ', '.&nbsp;')
            
            # Truncate long titles
            if len(title) > 60:
                title = title[:57] + "..."
            
            # Get community (subreddit) information
            subreddit = post.get('subreddit', 'N/A')
            subreddit_url = f"https://www.reddit.com/r/{subreddit}"
            community_link = f"[r/{subreddit}]({subreddit_url})"
            
            score = post.get('score', 0)
            comments = post.get('num_comments', 0)
            category = post.get('link_flair_text', 'N/A')
            if not category or category == 'None':
                category = 'General'
            
            # Format the timestamp
            created_utc = post.get('created_utc')
            if created_utc:
                if isinstance(created_utc, str):
                    try:
                        created_utc = datetime.fromisoformat(created_utc.replace('Z', '+00:00'))
                    except ValueError:
                        created_utc = datetime.utcnow()
                posted_time = created_utc.strftime("%Y-%m-%d %H:%M UTC")
            else:
                posted_time = 'N/A'
            
            # Create post URL
            post_id = post.get('post_id', '')
            post_url = f"https://www.reddit.com/comments/{post_id}"
            
            # Add row to table
            table += f"| {i} | [{title}]({post_url}) | {community_link} | {score} | {comments} | {category} | {posted_time} |\n"
        
        return table
    
    def _create_trending_posts_table(self, posts: List[Dict[str, Any]]) -> str:
        """
        Create a markdown table of trending posts from the last 24 hours.
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Markdown table as a string
        """
        # Sort posts by score (descending)
        sorted_posts = sorted(posts, key=lambda x: x.get('score', 0), reverse=True)
        
        # Filter posts with more than 10 comments
        filtered_posts = [post for post in sorted_posts if post.get('num_comments', 0) > 10]
        
        # Take top 10 posts
        top_posts = filtered_posts[:10]
        
        # Create table header
        table = "## Trending Posts - Last 24 Hours\n\n"
        table += "| Title | Community | Score | Comments | Category | Posted |\n"
        table += "|-------|-----------|-------|----------|----------|--------|\n"
        
        # Add rows to table
        for post in top_posts:
            title = post.get('title', 'N/A')
            
            # Enhanced title processing to prevent Markdown formatting issues
            # 1. Replace pipe characters that would break table formatting
            title = title.replace('|', '&#124;')
            
            # 2. Escape all brackets to prevent Markdown link interpretation
            title = title.replace('[', '\\[').replace(']', '\\]')
            
            # 3. Escape quotes to prevent string interpretation issues
            title = title.replace('"', '\\"').replace("'", "\\'")
            
            # 4. Replace any newline characters or carriage returns that might be in the title
            title = title.replace('\n', ' ').replace('\r', ' ')
            
            # 5. Replace periods followed by spaces with periods and non-breaking spaces
            # to prevent line breaks after periods
            title = title.replace('. ', '.&nbsp;')
            
            # Truncate long titles
            if len(title) > 60:
                title = title[:57] + "..."
            
            # Get community (subreddit) information
            subreddit = post.get('subreddit', 'N/A')
            subreddit_url = f"https://www.reddit.com/r/{subreddit}"
            community_link = f"[r/{subreddit}]({subreddit_url})"
            
            score = post.get('score', 0)
            comments = post.get('num_comments', 0)
            category = post.get('link_flair_text', 'N/A')
            if not category or category == 'None':
                category = 'General'
            
            # Format the timestamp
            created_utc = post.get('created_utc')
            if created_utc:
                if isinstance(created_utc, str):
                    try:
                        created_utc = datetime.fromisoformat(created_utc.replace('Z', '+00:00'))
                    except ValueError:
                        created_utc = datetime.utcnow()
                posted_time = created_utc.strftime("%Y-%m-%d %H:%M UTC")
            else:
                posted_time = 'N/A'
            
            # Create post URL
            post_id = post.get('post_id', '')
            post_url = f"https://www.reddit.com/comments/{post_id}"
            
            # Add row to table
            table += f"| [{title}]({post_url}) | {community_link} | {score} | {comments} | {category} | {posted_time} |\n"
        
        return table
    
    def _create_long_term_popular_table(self, posts: List[Dict[str, Any]], previous_report: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a table of popular posts from the last week/month with comparison data.
        
        Args:
            posts: List of post dictionaries
            previous_report: Previous report data for comparison
            
        Returns:
            Markdown table as a string
        """
        # Get posts from the last week
        week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_posts = []
        
        for post in posts:
            created_utc = post.get('created_utc')
            if created_utc:
                if isinstance(created_utc, str):
                    try:
                        created_utc = datetime.fromisoformat(created_utc.replace('Z', '+00:00'))
                    except ValueError:
                        continue
                
                if created_utc >= week_ago:
                    weekly_posts.append(post)
        
        # Sort weekly posts by score (descending)
        weekly_posts = sorted(weekly_posts, key=lambda x: x.get('score', 0), reverse=True)
        
        # Take top 5 weekly posts
        top_weekly = weekly_posts[:5]
        
        # Create table header
        table = "## Popular Posts (Last Week)\n\n"
        table += "| Title | Current Score | Previous Score | Change | Current Comments | Previous Comments | Change |\n"
        table += "|-------|---------------|----------------|--------|------------------|-------------------|--------|\n"
        
        # Add rows to table
        for post in top_weekly:
            title = post.get('title', 'N/A')
            if len(title) > 50:
                title = title[:47] + "..."
            
            current_score = post.get('score', 0)
            current_comments = post.get('num_comments', 0)
            
            # Get previous data if available
            previous_score = 0
            previous_comments = 0
            
            post_id = post.get('post_id', '')
            if previous_report and 'posts_data' in previous_report:
                for prev_post in previous_report['posts_data']:
                    if prev_post.get('post_id') == post_id:
                        previous_score = prev_post.get('score', 0)
                        previous_comments = prev_post.get('num_comments', 0)
                        break
            
            # Calculate changes
            score_change = current_score - previous_score
            comments_change = current_comments - previous_comments
            
            # Format changes
            if score_change > 0:
                score_change_str = f"+{score_change} 📈"
            elif score_change < 0:
                score_change_str = f"{score_change} 📉"
            else:
                score_change_str = "0"
            
            if comments_change > 0:
                comments_change_str = f"+{comments_change} 📈"
            elif comments_change < 0:
                comments_change_str = f"{comments_change} 📉"
            else:
                comments_change_str = "0"
            
            # Create post URL
            post_url = f"https://www.reddit.com/comments/{post_id}"
            
            # Add row to table
            table += f"| [{title}]({post_url}) | {current_score} | {previous_score} | {score_change_str} | {current_comments} | {previous_comments} | {comments_change_str} |\n"
        
        return table
    
    def _create_community_top_posts_tables(self, posts: List[Dict[str, Any]]) -> str:
        """
        Create tables showing top 3 posts from each community for the past week.
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Markdown tables as a string
        """
        # Filter posts from the last week
        week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_posts = []
        
        for post in posts:
            created_utc = post.get('created_utc')
            if created_utc:
                if isinstance(created_utc, str):
                    try:
                        created_utc = datetime.fromisoformat(created_utc.replace('Z', '+00:00'))
                    except ValueError:
                        continue
                
                if created_utc >= week_ago:
                    weekly_posts.append(post)
        
        # Group posts by subreddit
        communities = {}
        for post in weekly_posts:
            subreddit = post.get('subreddit')
            if not subreddit:
                continue
                
            if subreddit not in communities:
                communities[subreddit] = []
            
            communities[subreddit].append(post)
        
        # Sort communities alphabetically
        sorted_communities = sorted(communities.keys())
        
        # Create tables for each community
        all_tables = "## Top Posts by Community\n\n"
        
        for community in sorted_communities:
            # Sort posts by score (descending)
            sorted_posts = sorted(communities[community], key=lambda x: x.get('score', 0), reverse=True)
            
            # Take top 3 posts
            top_posts = sorted_posts[:3]
            
            # Skip if no posts
            if not top_posts:
                continue
            
            # Create table header
            all_tables += f"### r/{community}\n\n"
            all_tables += "| Title | Score | Comments | Category | Posted |\n"
            all_tables += "|-------|-------|----------|----------|--------|\n"
            
            # Add rows to table
            for post in top_posts:
                title = post.get('title', 'N/A')
                
                # Enhanced title processing to prevent Markdown formatting issues
                # 1. Replace pipe characters that would break table formatting
                title = title.replace('|', '&#124;')
                
                # 2. Escape all brackets to prevent Markdown link interpretation
                title = title.replace('[', '\\[').replace(']', '\\]')
                
                # 3. Escape quotes to prevent string interpretation issues
                title = title.replace('"', '\\"').replace("'", "\\'")
                
                # 4. Replace any newline characters or carriage returns that might be in the title
                title = title.replace('\n', ' ').replace('\r', ' ')
                
                # 5. Replace periods followed by spaces with periods and non-breaking spaces
                # to prevent line breaks after periods
                title = title.replace('. ', '.&nbsp;')
                
                # Truncate long titles
                if len(title) > 60:
                    title = title[:57] + "..."
                
                score = post.get('score', 0)
                comments = post.get('num_comments', 0)
                category = post.get('link_flair_text', 'N/A')
                if not category or category == 'None':
                    category = 'General'
                
                # Format the timestamp
                created_utc = post.get('created_utc')
                if created_utc:
                    if isinstance(created_utc, str):
                        try:
                            created_utc = datetime.fromisoformat(created_utc.replace('Z', '+00:00'))
                        except ValueError:
                            created_utc = datetime.utcnow()
                    posted_time = created_utc.strftime("%Y-%m-%d %H:%M UTC")
                else:
                    posted_time = 'N/A'
                
                # Create post URL
                post_id = post.get('post_id', '')
                post_url = f"https://www.reddit.com/comments/{post_id}"
                
                # Add row to table
                all_tables += f"| [{title}]({post_url}) | {score} | {comments} | {category} | {posted_time} |\n"
            
            # Add spacing between tables
            all_tables += "\n\n"
        
        return all_tables
    
    def generate_report(self, posts: List[Dict[str, Any]], previous_report: Optional[Dict[str, Any]] = None, 
                       weekly_posts: Optional[List[Dict[str, Any]]] = None, 
                       monthly_posts: Optional[List[Dict[str, Any]]] = None,
                       language: str = "en",
                       reference_date: Optional[datetime] = None) -> str:
        """
        Generate a report from Reddit posts using the Groq API.
        
        Args:
            posts: List of post dictionaries (24-hour trending posts)
            previous_report: Previous report data for comparison
            weekly_posts: List of weekly popular posts
            monthly_posts: List of monthly popular posts
            language: Language for the report ('en' for English, 'zh' for Chinese)
            reference_date: Optional specific date to generate report for (defaults to current date)
            
        Returns:
            Generated report as a string
        """
        logger.info(f"Generating report from {len(posts)} posts using Groq API in {language} language")
        
        # Use reference date or current date
        report_date = reference_date if reference_date is not None else datetime.now()
        current_date = report_date.strftime("%Y-%m-%d")
        
        # Create monthly popular posts table if provided
        monthly_table = ""
        if monthly_posts:
            monthly_table = self._create_monthly_popular_table(monthly_posts, previous_report)
        
        # Create weekly popular posts table if provided
        weekly_table = ""
        if weekly_posts:
            weekly_table = self._create_weekly_popular_table(weekly_posts, previous_report)
        
        # Create trending posts table
        trending_table = self._create_trending_posts_table(posts)
        
        # Create community top posts tables
        community_tables = self._create_community_top_posts_tables(posts)
        
        # Prepare post data for analysis
        post_data = []
        for post in posts:
            post_data.append({
                "title": post.get('title', ''),
                "score": post.get('score', 0),
                "num_comments": post.get('num_comments', 0),
                "url": post.get('url', ''),
                "selftext": post.get('selftext', '')[:500] if post.get('selftext') else '',
                "created_utc": str(post.get('created_utc', '')),
                "subreddit": post.get('subreddit', ''),
                "link_flair_text": post.get('link_flair_text', '')
            })
        
        # Define language-specific content
        if language == "zh":
            # Chinese prompt and headers
            section_headers = {
                "report_title": f"# Reddit 数字金融 趋势报告 - {current_date}",
                "trending_posts": "## 今日热门帖子",
                "weekly_posts": "## 本周热门帖子",
                "monthly_posts": "## 本月热门帖子",
                "community_posts": "## 各社区本周热门帖子",
                "trend_analysis": "## 趋势分析"
            }
            
            prompt = f"""
            您是一位专门分析Reddit趋势的数字金融和数字货币的技术分析师。您的任务是分析来自数字金融和数字货币相关subreddit的最新帖子，并为{current_date}生成一份全面的报告。不用提供报告标题，只需专注于内容。

            以下是热门和趋势帖子的表格：
            
            {trending_table}
            
            {weekly_table}
            
            {monthly_table}
            
            {community_tables}
            
            根据这些帖子，请提供：
            
            1. **今日焦点**：分析过去24小时内出现的最新趋势和突破性发展。重点关注今天新出现的、与之前周趋势和月趋势不同的新兴话题。引用具体的帖子作为例证，并解释为什么这些新趋势值得关注。这是报告中最重要的部分，应该占据报告的主要篇幅。
            
            2. **周趋势对比**：将今日趋势与过去一周的趋势进行对比分析。哪些趋势持续存在？哪些是新出现的？这些变化反映了社区兴趣的什么变化？
            
            3. **月度技术演进**：从更长远的角度，分析当前趋势如何融入或改变了过去一个月的技术发展路线。特别关注那些可能代表数字金融和数字货币领域重大转变的新兴技术或方法。

            4. **技术深度解析**：选择一个特别有趣或重要的今日趋势，提供更详细的技术解释，包括它是什么、为什么重要、以及它与更广泛的数字金融和数字货币生态系统的关系。
            
            5. **社区亮点**：分析过去一周内不同社区（subreddit）的热门话题有何不同，各个社区关注的重点是什么，以及这些社区之间的交叉话题。特别关注那些在大型社区之外的小型社区中出现的独特讨论和见解。

            您的分析应该简洁、有见地，并专注于对数字金融和数字货币专业人士有用的可操作信息。避免一般性陈述，而是提供基于帖子数据的具体见解。特别强调今日的新发现和突破，同时将其放在周趋势和月趋势的背景下进行分析。

            请用中文回答。
            """
        else:
            # English (default) prompt and headers
            section_headers = {
                "report_title": f"# Reddit AI Trend Report - {current_date}",
                "trending_posts": "## Today's Trending Posts",
                "weekly_posts": "## Weekly Popular Posts",
                "monthly_posts": "## Monthly Popular Posts",
                "community_posts": "## Top Posts by Community (Past Week)",
                "trend_analysis": "## Trend Analysis"
            }
            
            prompt = f"""
            You are an AI technology analyst specializing in Reddit trend analysis. Your task is to analyze recent posts from AI-related subreddits and generate a comprehensive report for {current_date}. Do not provide a report title, just focus on the content.

            Below are the tables of popular and trending posts:
            
            {trending_table}
            
            {weekly_table}
            
            {monthly_table}
            
            {community_tables}
            
            Based on these posts, please provide:
            
            1. **Today's Highlights**: Analyze the latest trends and breakthrough developments that have emerged in the past 24 hours. Focus on new emerging topics that differ from the previous weekly and monthly trends. Reference specific posts as examples and explain why these new trends are worth attention. This is the most important part of the report and should occupy the main portion.
            
            2. **Weekly Trend Comparison**: Compare today's trends with those from the past week. Which trends persist? Which ones are newly emerging? What do these changes reflect about shifting interests in the AI community?
            
            3. **Monthly Technology Evolution**: From a longer-term perspective, analyze how current trends fit into or change the technological development path of the past month. Pay special attention to emerging technologies or methods that may represent significant shifts in the AI field.
            
            4. **Technical Deep Dive**: Select a particularly interesting or important trend from today and provide a more detailed technical explanation, including what it is, why it's important, and its relationship to the broader AI ecosystem.
            
            5. **Community Highlights**: Analyze how the hot topics from the past week differ across communities (subreddits), what each community is focusing on, and what cross-cutting topics appear across communities. Pay special attention to unique discussions and insights emerging from smaller communities beyond the major ones.
            
            Your analysis should be concise, insightful, and focused on actionable information useful to AI professionals. Avoid general statements and instead provide specific insights based on the post data. Particularly emphasize today's new discoveries and breakthroughs, while analyzing them in the context of weekly and monthly trends.
            
            Please respond in English.
            """
        
        try:
            # Generate the report
            report = self.generate_text(prompt)
            
            # Add header and tables
            full_report = f"{section_headers['report_title']}\n\n"
            full_report += f"{section_headers['trend_analysis']}\n\n"
            full_report += report + "\n\n"
            full_report += f"{section_headers['trending_posts']}\n\n"
            full_report += trending_table.replace("## Trending Posts - Last 24 Hours\n\n", "") + "\n\n"
            full_report += f"{section_headers['weekly_posts']}\n\n"
            full_report += weekly_table.replace("## Weekly Popular Posts\n\n", "") + "\n\n"
            full_report += f"{section_headers['monthly_posts']}\n\n"
            full_report += monthly_table.replace("## Monthly Popular Posts\n\n", "") + "\n\n"
            full_report += f"{section_headers['community_posts']}\n\n"
            full_report += community_tables.replace("## Top Posts by Community\n\n", "") + "\n\n"

            return full_report
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"Error generating report: {e}"
            
    def generate_multilingual_reports(self, posts: List[Dict[str, Any]], previous_data: Optional[Dict[str, Any]] = None, 
                                     weekly_posts: Optional[List[Dict[str, Any]]] = None, 
                                     monthly_posts: Optional[List[Dict[str, Any]]] = None,
                                     languages: List[str] = ["en", "zh"],
                                     reference_date: Optional[datetime] = None) -> Dict[str, str]:
        """
        Generate reports in multiple languages.
        
        Args:
            posts: List of post dictionaries (24-hour trending posts)
            previous_data: Optional dictionary containing previous report data for comparison
            weekly_posts: List of weekly popular posts
            monthly_posts: List of monthly popular posts
            languages: List of language codes to generate reports for
            reference_date: Optional specific date to generate report for (defaults to current date)
            
        Returns:
            Dictionary mapping language codes to generated reports
        """
        reports = {}
        
        for lang in languages:
            logger.info(f"Generating report in {lang} language")
            report = self.generate_report(posts, previous_data, weekly_posts, monthly_posts, language=lang, reference_date=reference_date)
            reports[lang] = report
            
