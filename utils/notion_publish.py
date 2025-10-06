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
        self.NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

        self.headers = {
            "Authorization": f"Bearer {self.NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": "2025-09-03"
        }

    def chunk_text(text, chunk_size=1000):
        """将长文本切分成小块，避免超过 Notion API 限制"""
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    def publish_markdown_to_notion(self, md_content, title="Daily Note"):
        url = "https://api.notion.com/v1/pages"

        # 把长文本切分
        chunks = self.chunk_text(md_content, 2000)

        # 每个小块转成一个 Notion paragraph block
        children = []
        for chunk in chunks:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                }
            })

        data = {
            "parent": {"database_id": self.NOTION_DATABASE_ID},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": title}}]
                }
            },
            "children": children
        }

        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code == 200:
            print("✅ 成功发布到 Notion")
        else:
            print("❌ 发布失败:", response.text)