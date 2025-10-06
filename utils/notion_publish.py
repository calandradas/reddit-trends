import os
import requests
import schedule
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class NotionPublisher:
    def __init__(self):
        self.NOTION_API_KEY = os.getenv("NOTION_API_KEY")
        self.DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

        self.headers = {
            "Authorization": f"Bearer {self.NOTION_API_KEY}",
            "Content-Type": "application/json"
        }

    def publish_markdown_to_notion(md_content, title="Daily Note"):
        """将 Markdown 内容作为 Notion 页面发布到指定数据库"""
        url = "https://api.notion.com/v1/pages"
        data = {
            "parent": {"database_id": DATABASE_ID},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": title}}]
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": md_content}}]
                    }
                }
            ]
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print("✅ 成功发布到 Notion")
        else:
            print("❌ 发布失败:", response.text)
