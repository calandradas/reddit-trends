"""
Reddit Data Collector

This module provides a unified interface for collecting Reddit data,
combining the functionality of community_fetch and post_detail_fetch.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from services.reddit_collection.community_fetch import RedditCommunityFetcher
from services.reddit_collection.post_detail_fetch import RedditPostDetailFetcher
from database.mongodb import MongoDBClient
from config import REDDIT_COMMUNITIES, EXCLUDED_CATEGORIES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RedditDataCollector:
    """Service for collecting and storing Reddit data."""
    
    def __init__(self, db_client: Optional[MongoDBClient] = None):
        """
        Initialize the Reddit data collector.
        
        Args:
            db_client: MongoDB client for storing data (optional)
        """
        self.community_fetcher = RedditCommunityFetcher()
        self.post_detail_fetcher = RedditPostDetailFetcher()
        self.db_client = db_client
        
        logger.info("Reddit data collector initialized")
        if EXCLUDED_CATEGORIES:
            logger.info(f"Excluding posts with categories: {', '.join(EXCLUDED_CATEGORIES)}")
    
    def collect_community_data(self, subreddit_name: str) -> Dict[str, Any]:
        """
        Collect data from a specific subreddit.
        
        Args:
            subreddit_name: Name of the subreddit
            
        Returns:
            Dictionary containing community data and posts
        """
        logger.info(f"Collecting data from r/{subreddit_name}")
        
        # Get community summary
        community_info = self.community_fetcher.get_community_summary(subreddit_name)
        
        # Get trending posts for all timeframes
        posts_data = self.community_fetcher.fetch_all_timeframes(subreddit_name)
        
        # Combine data
        community_data = {
            "community_info": community_info,
            "posts": posts_data
        }
        
        # Store data in MongoDB if client is provided
        if self.db_client:
            self.db_client.store_community_data(community_data)
        
        logger.info(f"Successfully collected data from r/{subreddit_name}")
        return community_data
    
    def collect_post_details(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Collect detailed information about a specific post.
        
        Args:
            post_id: ID of the post
            
        Returns:
            Dictionary containing post details, or None if post not found
        """
        logger.info(f"Collecting details for post {post_id}")
        
        # Get post details
        post_details = self.post_detail_fetcher.get_post_details(post_id)
        
        # Store data in MongoDB if client is provided
        if post_details and self.db_client:
            self.db_client.store_post_details(post_details)
        
        logger.info(f"Successfully collected details for post {post_id}")
        return post_details
    
    def collect_trending_posts(self, time_range_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Collect trending posts from multiple subreddits within a specific time range.
        
        Args:
            time_range_hours: Time range in hours
            
        Returns:
            List of trending posts
        """
        logger.info(f"Collecting trending posts from the last {time_range_hours} hours")
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        all_trending_posts = []
        
        # Collect posts from each subreddit
        for subreddit_name in REDDIT_COMMUNITIES:
            # Get trending posts
            posts = self.community_fetcher.get_trending_posts(
                subreddit_name=subreddit_name,
                time_filter="day" if time_range_hours <= 24 else "week",
                limit=50
            )
            
            # Filter posts by time range
            filtered_posts = []
            for post in posts:
                created_utc = post.get('created_utc')
                if created_utc and start_time <= created_utc <= end_time:
                    filtered_posts.append(post)
            
            logger.info(f"Collected {len(filtered_posts)} trending posts from r/{subreddit_name}")
            all_trending_posts.extend(filtered_posts)
        
        # Sort posts by score (descending)
        sorted_posts = sorted(all_trending_posts, key=lambda x: x.get('score', 0), reverse=True)
        
        # Store data in MongoDB if client is provided
        if self.db_client:
            self.db_client.store_trending_posts(sorted_posts, time_range_hours)
        
        logger.info(f"Successfully collected {len(sorted_posts)} trending posts")
        return sorted_posts
    
    # 添加与report_generation.py和test_report_generation.py兼容的方法
    
    def get_subreddit_posts(self, subreddit: str, limit: int = 100, time_filter: str = "week") -> List[Dict[str, Any]]:
        """
        Get posts from a specific subreddit.
        
        Args:
            subreddit: Name of the subreddit
            limit: Maximum number of posts to return
            time_filter: Time filter for posts (hour, day, week, month, year, all)
            
        Returns:
            List of post dictionaries
        """
        logger.info(f"Getting posts from r/{subreddit} (limit: {limit}, time_filter: {time_filter})")
        
        # 使用community_fetcher获取帖子
        posts = self.community_fetcher.get_trending_posts(
            subreddit_name=subreddit,
            time_filter=time_filter,
            limit=limit
        )
        
        logger.info(f"Got {len(posts)} posts from r/{subreddit}")
        return posts
    
    def get_weekly_popular_posts(self, subreddits: List[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get the most popular posts from the last week.
        
        Args:
            subreddits: List of subreddits to collect from (defaults to config)
            limit: Maximum number of posts to return
            
        Returns:
            List of post dictionaries
        """
        logger.info(f"Getting weekly popular posts (limit: {limit})")
        
        # 使用默认subreddits（如果未提供）
        if not subreddits:
            subreddits = REDDIT_COMMUNITIES
        
        all_posts = []
        for subreddit in subreddits:
            # 获取每周热门帖子
            posts = self.community_fetcher.get_trending_posts(
                subreddit_name=subreddit,
                time_filter="week",
                limit=limit
            )
            
            all_posts.extend(posts)
        
        # 按分数排序（降序）并获取前limit个帖子
        sorted_posts = sorted(all_posts, key=lambda x: x.get('score', 0), reverse=True)
        top_posts = sorted_posts[:limit]
        
        logger.info(f"Got {len(top_posts)} weekly popular posts")
        return top_posts
    
    def get_monthly_popular_posts(self, subreddits: List[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get the most popular posts from the last month.
        
        Args:
            subreddits: List of subreddits to collect from (defaults to config)
            limit: Maximum number of posts to return
            
        Returns:
            List of post dictionaries
        """
        logger.info(f"Getting monthly popular posts (limit: {limit})")
        
        # 使用默认subreddits（如果未提供）
        if not subreddits:
            subreddits = REDDIT_COMMUNITIES
        
        all_posts = []
        for subreddit in subreddits:
            # 获取每月热门帖子
            posts = self.community_fetcher.get_trending_posts(
                subreddit_name=subreddit,
                time_filter="month",
                limit=limit
            )
            
            all_posts.extend(posts)
        
        # 按分数排序（降序）并获取前limit个帖子
        sorted_posts = sorted(all_posts, key=lambda x: x.get('score', 0), reverse=True)
        top_posts = sorted_posts[:limit]
        
        logger.info(f"Got {len(top_posts)} monthly popular posts")
        return top_posts
    
    def filter_posts_by_category(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤掉指定类别的帖子
        
        Args:
            posts: 帖子列表
            
        Returns:
            过滤后的帖子列表
        """
        if not EXCLUDED_CATEGORIES:
            return posts
            
        filtered_posts = []
        for post in posts:
            category = post.get('category')
            if category and category in EXCLUDED_CATEGORIES:
                logger.info(f"排除类别为 '{category}' 的帖子: {post.get('title', '无标题')}")
                continue
            filtered_posts.append(post)
            
        logger.info(f"过滤前帖子数: {len(posts)}, 过滤后帖子数: {len(filtered_posts)}")
        return filtered_posts
        
    def collect_data_from_all_communities(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Collect data from all configured communities.
        
        Args:
            hours: Number of hours to look back for posts
            
        Returns:
            List of all collected posts
        """
        all_posts = []
        
        # Process high priority communities
        for subreddit, limit in REDDIT_COMMUNITIES.get("high_priority", {}).items():
            try:
                community_data = self.collect_community_data(subreddit)
                posts = self.post_detail_fetcher.fetch_post_details(
                    community_data["posts"][:limit], 
                    subreddit
                )
                all_posts.extend(posts)
            except Exception as e:
                logger.error(f"Error collecting data from r/{subreddit}: {e}")
        
        # Process medium priority communities
        for subreddit, limit in REDDIT_COMMUNITIES.get("medium_priority", {}).items():
            try:
                community_data = self.collect_community_data(subreddit)
                posts = self.post_detail_fetcher.fetch_post_details(
                    community_data["posts"][:limit], 
                    subreddit
                )
                all_posts.extend(posts)
            except Exception as e:
                logger.error(f"Error collecting data from r/{subreddit}: {e}")
        
        # Filter posts by time
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_posts = [
            post for post in all_posts 
            if post.get("created_utc") and datetime.fromtimestamp(post["created_utc"]) > cutoff_time
        ]
        
        # 过滤掉排除类别的帖子
        filtered_posts = self.filter_posts_by_category(recent_posts)
        
        logger.info(f"Collected {len(filtered_posts)} posts from all communities in the last {hours} hours")
        
        # Store in database if client is provided
        if self.db_client:
            for post in filtered_posts:
                self.db_client.save_post(post)
            logger.info(f"Saved {len(filtered_posts)} posts to database")
        
        return filtered_posts 