import os
from dotenv import load_dotenv
from datetime import datetime
from telegram import Bot
import logging
# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.bot = Bot(token=self.token)

    async def send_daily_report(self, report):
        """Send daily report to the chat."""
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=self._escape_markdown(report), parse_mode='MarkdownV2')
            logger.info(f"Report sent at {datetime.now()}")
        except Exception as e:
            logger.error(f"Error sending to telegram report: {e}")
    
    def _escape_markdown(self, text: str) -> str:
        """Escape reserved MarkdownV2 characters in the report."""
        reserved_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in reserved_chars:
            text = text.replace(char, f'\\{char}')
        return text
