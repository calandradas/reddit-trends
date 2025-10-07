import asyncio
import os
from dotenv import load_dotenv
from notion_client import Client
from notionary import NotionPage
from notionary.database import NotionDatabase


class NotionPublisher:
    def __init__(self, overwrite=False):
        load_dotenv()
        self.api_key = os.getenv("NOTION_API_KEY")
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        self.overwrite = overwrite
        self.notion_version = os.getenv("NOTION_VERSION", "2022-06-28")

        if not self.api_key or not self.database_id:
            raise ValueError("请设置 NOTION_API_KEY 和 NOTION_DATABASE_ID")
        self.notion = Client(auth=self.api_key, notion_version=self.notion_version)

    def _find_duplicates(self, title: str):
        """查询是否已有相同标题的页面"""
        try:
            resp = self.notion.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Name",
                    "title": {"equals": title}
                }
            )
        except Exception as e:
            print(f"查询失败: {e}")

        results = resp.get("results", [])
        if not results:
            print(f"未发现同名页面: {title}")
        else:
            print(f"发现同名页面: {title}")
        return results

    def _archive_page(self, page_id: str):
        return self.notion.pages.update(page_id=page_id, archived=True)

    def _delete_duplicates(self, title: str):
        pages = self._find_duplicates(title)
        for p in pages:
            print("删除旧页面: {title}")
            self._archive_page(p["id"])
        return len(pages)
    
    async def create_page(self, title, industry, language, date_str, md_content=None):
        try:
            client = await NotionDatabase.from_database_id(token=self.api_key, id=self.database_id)
            page = await client.create_blank_page()
            await page.append_markdown(md_content)
            await page.set_title(title)
            await page.set_property_value_by_name("Industry", industry)
            await page.set_property_value_by_name("Language", language)
            await page.set_property_value_by_name("Create Date", date_str + "UTC")
            """ properties = {
                "Name": {"title": [{"type": "text", "text": {"content": title}}]},
                "Industry": {"rich_text": [{"type": "text", "text": {"content": industry}}]},
                "Language": {"rich_text": [{"type": "text", "text": {"content": language}}]},
                "Create Date": {"rich_text": [{"type": "text", "text": {"content": date_str + "UTC"}}]}
            } 
            resp = self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=children
            )"""
            print("上传成功")
        except Exception as e:
            print(f"上传失败: {e}")
            return None
        return True

    def publish(self, md_content=None, title="Daily Note", date=None, language="en", industry="ai"):
        """如果标题相同则删除式覆盖，否则直接新建"""
        if self.overwrite:
            len = self._delete_duplicates(title)
            print(f"共删除 {len} 个页面")
        # 不论是否删除，都创建新页面
        print(f"创建新页面: {title}")
        resp = asyncio.run(self.create_page(title=title, industry=industry, language=language, date_str=date, md_content=md_content))
        if resp:
            print("成功发布到 Notion")
        else:
            print("发布失败:", resp.text)                
