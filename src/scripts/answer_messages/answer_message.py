import types
from typing import Dict, Any

from aiogram import Bot
from aiogram.types import FSInputFile, InputMediaPhoto, URLInputFile

from src.bot.keyboards.select_gpt import upgrade_message, upgrade_photo
from src.config.config import settings
from src.utils.logger import setup_logger


class AnswerMessage:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.bot = Bot(token=settings.BOT_API)


    async def get_db_session(self):
        ...

    async def _remove_energy(self):
        ...

    async def answer_message(self, data: Dict[str, Any]) -> None:
        try:
            if not data.get("text"):
                data["text"] = "⚠ Произошла ошибка при генерации"

            await self.bot.edit_message_text(chat_id=data['user_id'], message_id=data['answer_message'], text=data['text'], reply_markup=upgrade_message())

        except Exception as e:
            self.logger.error(f"Failed to answer message: {e}")
            raise

    async def answer_photo(self, data: Dict[str, Any]) -> None:
        try:
            if not data.get("photo"):
                data["text"] = "⚠ Произошла ошибка при генерации"
                await self.bot.edit_message_text(chat_id=data['user_id'], message_id=data['answer_message'], text=data['text'],
                                                 reply_markup=upgrade_message())

            if isinstance(data["photo"], bytes):
                file_path = "/tmp/temp_image.jpg"
                with open(file_path, "wb") as f:
                    f.write(data["photo"])

                photo = InputMediaPhoto(media=FSInputFile(file_path))
            else:
                # Если это URL
                photo = InputMediaPhoto(media=data["photo"])

            await self.bot.edit_message_media(chat_id=data["user_id"], message_id=data["answer_message"], media=photo)
            await self.bot.edit_message_caption(chat_id=data["user_id"], message_id=data["answer_message"], caption="Ваше сгенерированое фото, выберите одно из действий снизу:",
                                                reply_markup=upgrade_photo())

        except Exception as e:
            self.logger.error(f"Failed to answer photo: {e}")
            raise