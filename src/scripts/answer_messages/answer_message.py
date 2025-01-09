import types
from typing import Dict, Any

from aiogram import Bot

from src.bot.keyboards.select_gpt import upgrade_message
from src.config.config import settings
from src.utils.logger import setup_logger


class AnswerMessage:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.bot = Bot(token=settings.BOT_API)

    async def _remove_energy(self):
        ...

    async def answer_message(self, data: Dict[str, Any]):
        try:
            await self.bot.edit_message_text(chat_id=data['user_id'], message_id=data['answer_message'], text=data['text'], reply_markup=upgrade_message())

        except Exception as e:
            self.logger.error(f"Failed to answer message: {e}")
            raise
