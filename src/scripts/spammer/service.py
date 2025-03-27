from typing import Any

from aiogram import Bot
from aiogram.types import FSInputFile

from src.utils.logger import setup_logger
from src.config.config import settings
from src.db.orm.user_orm import UserORM
from src.utils.redis_cache.redis_cache import redis_manager


class TelegramBroadcaster:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.timeout = [30]
        self._bot = Bot(token=settings.BOT_API)

    async def broadcast(
        self,
        text: str = "-",
        photo_path: str = None,
        premium_only: bool = False,
        not_premium_only: bool = False,
    ):
        """Рассылка"""
        spam_key = await redis_manager.get(f"spam_key:{text}")

        user_ids = await self._get_user_ids(
            premium_only=premium_only,
            not_premium_only=not_premium_only,
        )

        data = {"get_users_ids": user_ids, "send_message": 0}
        spam_key = await redis_manager.set(
            "spam_key", value=data
        )

        for user_id in user_ids:
            try:
                if photo_path:
                    success = await self.send_message_with_photo(
                        user_id=user_id, message=text, photo=photo_path
                    )
                else:
                    success = await self.send_message(message=text, user_id=user_id)
                data["send_message"] += 1
                self.logger.debug(data)
            except Exception as e:
                self.logger.error(e)
                continue

    async def send_message(self, message: str, user_id: int) -> dict[str, Any]:
        """Отправка сообщений пользователю"""
        try:
            await self._bot.send_message(chat_id=user_id, text=message)
            return {"send": True, "user_id": user_id}
        except Exception as e:
            self.logger.error(e)
            return {"send": False, "error": e, "user_id": user_id}

    async def send_message_with_photo(self, user_id: int, message: str, photo: str):
        """Отправка сообщения пользователю с фотографией"""
        try:
            photo = FSInputFile(photo)
            await self._bot.send_photo(chat_id=user_id, photo=photo, caption=message)
            return {"send": True, "user_id": user_id}
        except Exception as e:
            self.logger.error(e)
            return {"send": False, "error": e, "user_id": user_id}

    async def _get_user_ids(
        self, premium_only: bool = False, not_premium_only: bool = False
    ) -> list[int]:
        """Получение пользователей"""

        users = await UserORM.get_users_ids(
            premium_only=premium_only,
            not_premium_only=not_premium_only,
        )

        return users
