import os
import requests
import markdown
from bs4 import BeautifulSoup
from dotenv import load_dotenv

class NotionPublisher:
    def __init__(self, overwrite=False):
        load_dotenv()
        self.api_key = os.getenv("NOTION_API_KEY")
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        self.overwrite = overwrite
        self.notion_version = os.getenv("NOTION_VERSION", "2025-09-03")

        if not self.api_key or not self.database_id:
            raise ValueError("请设置 NOTION_API_KEY 和 NOTION_DATABASE_ID")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.notion_version
        }

    @staticmethod
    def _chunk_text(text, chunk_size=1000):
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    def _markdown_to_notion_blocks(self, md_text):
        html = markdown.markdown(md_text)
        soup = BeautifulSoup(html, "html.parser")
        blocks = []

        for element in soup.children:
            if element.name is None:
                continue

            if element.name in ["h1", "h2", "h3"]:
                level = int(element.name[1])
                blocks.append({
                    "object": "block",
                    "type": f"heading_{level}",
                    f"heading_{level}": {
                        "rich_text": [{"type": "text", "text": {"content": element.get_text()}}]
                    }
                })

            elif element.name in ["ul", "ol"]:
                for li in element.find_all("li"):
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item" if element.name == "ul" else "numbered_list_item",
                        "bulleted_list_item" if element.name == "ul" else "numbered_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": li.get_text()}}]
                        }
                    })

            elif element.name == "pre":
                code = element.get_text()
                for chunk in self.chunk_text(text=code, chunk_size=1900):
                    blocks.append({
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [{"type": "text", "text": {"content": chunk}}],
                            "language": "python"
                        }
                    })

            elif element.name == "p":
                text = element.get_text()
                for chunk in self.chunk_text(text=text, chunk_size=1900):
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": chunk}}]
                        }
                    })

        return blocks

    def _find_page_by_title(self, title):
        """查询是否已有相同标题的页面"""
        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        query = {
            "filter": {
                "property": "Name",
                "title": {
                    "equals": title
                }
            }
        }
        resp = requests.post(url, headers=self.headers, json=query)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                return results[0]["id"]  # 返回第一个匹配页面的 ID
        return None

    def publish(self, md_content, title="Daily Note"):
        """如果标题相同则覆盖，否则新建"""
        existing_page_id = self.find_page_by_title(title)

        if existing_page_id and self.overwrite:
            print(f"发现同名页面，删除旧页面: {title}")
            resp = requests.patch(
                f"https://api.notion.com/v1/pages/{existing_page_id}",
                headers=self.headers,
                json={"archived": True}
            )
            if resp.status_code in [200, 201]:
                print("旧页面已删除")
            else:
                print("删除失败:", resp.text)
                return  # 删除失败就不继续新建            

        # 不论是否删除，都创建新页面
        print(f"创建新页面: {title}")
        url = "https://api.notion.com/v1/pages"
        children = self.markdown_to_notion_blocks(md_content)

        data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": title}}]
                }
            },
            "children": children
        }
        resp = requests.post(url, headers=self.headers, json=data)
        if resp.status_code in [200, 201]:
            print("成功发布到 Notion")
        else:
            print("发布失败:", resp.text)                
