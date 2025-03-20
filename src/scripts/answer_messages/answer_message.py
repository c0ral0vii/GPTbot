import types
from typing import Dict, Any

from aiogram import Bot
from aiogram.types import FSInputFile, InputMediaPhoto, URLInputFile

from src.bot.keyboards.select_gpt import upgrade_message, upgrade_photo
from src.config.config import settings
from src.db.orm.user_orm import UserORM
from src.utils.logger import setup_logger


class AnswerMessage:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.bot = Bot(token=settings.BOT_API)

    async def send_notification(self, data: Dict[str, Any]) -> bool:
        try:
            await self.bot.send_message(chat_id=data["user_id"], text=data["text"])
            return True
        except Exception as e:
            return False

    async def send_referral_message(self, data: Dict[str, Any]) -> None:
        try:
            await self.bot.send_message(chat_id=data["user_id"], text=data["text"])

            await UserORM.add_energy(data["user_id"], 20)
        except Exception as e:
            self.logger.error(e)
            return

    async def answer_message(self, data: Dict[str, Any]) -> None:
        try:
            if not data.get("text"):
                data["text"] = "⚠ Произошла ошибка при генерации"

            disable_delete = data.get("disable_delete", False)

            if disable_delete is True:
                delete = await self.bot.delete_message(
                    chat_id=data["user_id"], message_id=data["answer_message"]
                )

            await self.bot.send_message(
                chat_id=data["user_id"],
                text=data["text"],
                parse_mode="Markdown",
            )
            # reply_markup=await upgrade_message(),

            energy_text = data.get("energy_text", None)

            if energy_text:
                await self.bot.send_message(
                    chat_id=data["user_id"], text=data["energy_text"]
                )

        except Exception as e:
            self.logger.error(f"Failed to answer message: {e}")
            return

    async def answer_photo(self, data: Dict[str, Any]) -> None:
        try:
            if not data.get("photo"):
                data["text"] = "⚠ Произошла ошибка при генерации"
                await self.bot.edit_message_text(
                    chat_id=data["user_id"],
                    message_id=data["answer_message"],
                    text=data["text"],
                    reply_markup=await upgrade_message(),
                )

            if isinstance(data["photo"], bytes):
                file_path = "/tmp/temp_image.jpg"
                with open(file_path, "wb") as f:
                    f.write(data["photo"])

                photo = InputMediaPhoto(media=FSInputFile(file_path))
            else:
                # Если это URL
                photo = InputMediaPhoto(media=data["photo"])

            await self.bot.edit_message_media(
                chat_id=data["user_id"], message_id=data["answer_message"], media=photo
            )

            kb = data.get("keyboard")

            await self.bot.edit_message_caption(
                chat_id=data["user_id"],
                message_id=data["answer_message"],
                caption=(
                    f"<a href='{data['original_link']}'>Ссылка</a> на оригинал.\n\n"
                    f"Промпт: <code>{data['message']}</code>\n"
                    f"Модель: <code>#{data['type'].upper()}</code>\n"
                ),
                parse_mode="HTML",
                reply_markup=(
                    await upgrade_photo(image_id=data["image_id"])
                    if not kb
                    else data["keyboard"]
                ),
            )

            text = await UserORM.remove_energy(data["user_id"], data["energy_cost"])
            await self.bot.send_message(chat_id=data["user_id"], text=text["text"])
        except Exception as e:
            self.logger.error(f"Failed to answer photo: {e}", exc_info=True)
            return
