import os
from dotenv import load_dotenv
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
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
        self.token = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID')
        self.app = Application.builder().token(self.token).build()
        self.app.add_handler(CommandHandler("start", self.start))

    async def send_daily_report(self, report):
        """Send daily report to the chat."""
        try:
            await self.app.initialize()
            await self.app.start()
            await self.app.bot.send_message(chat_id=self.chat_id, text=report, parse_mode='MarkdownV2')
            await self.app.stop()
            await self.app.shutdown()
            logger.info(f"Report sent at {datetime.now()}")
        except Exception as e:
            logger.error(f"Error sending report: {e}")
