import asyncio
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
        self.MAX_MESSAGE_LENGTH = 4096  # Telegram's max message length

    async def send_daily_report(self, report):
        """Send daily report to the chat."""
        try:
            messages = self._split_message(self._escape_markdown(report))
            for i, msg in enumerate(messages, 1):
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=f"{msg}\n\nPart {i}/{len(messages)}" if len(messages) > 1 else msg,
                    parse_mode='MarkdownV2'
                )
                logger.info(f"Sent part {i}/{len(messages)} at {asyncio.get_event_loop().time():.2f}")
                await asyncio.sleep(1)  # Sleep to avoid hitting rate limits (20 messages per minute)
        except Exception as e:
            logger.error(f"Error sending to telegram report: {e}")
    
    def _escape_markdown(self, text: str) -> str:
        """Escape reserved MarkdownV2 characters in the report."""
        reserved_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in reserved_chars:
            text = text.replace(char, f'\\{char}')
        return text

    def _split_message(self, text: str) -> list[str]:
        """Split a message into chunks under MAX_MESSAGE_LENGTH, preserving lines."""
        if len(text) <= self.MAX_MESSAGE_LENGTH:
            return [text]
        
        messages = []
        current_message = ""
        lines = text.split('\n')
        
        for line in lines:
            # If adding the line exceeds the limit, save current_message and start a new one
            if len(current_message) + len(line) + 1 > self.MAX_MESSAGE_LENGTH:
                if current_message:
                    messages.append(current_message.strip())
                current_message = line + '\n'
            else:
                current_message += line + '\n'
        
        # Add the last chunk if it exists
        if current_message:
            messages.append(current_message.strip())
        
        return messages