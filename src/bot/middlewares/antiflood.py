from aiogram import BaseMiddleware, types
from src.utils.redis_cache.redis_cache import redis_manager


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.redis_client = redis_manager

    async def __call__(self, handler, event, data: dict):
        user = event.from_user
        if not user:
            return await handler(event, data)

        user_id = user.id
        key = f"rate_limit:{user_id}"

        # Check if the user has exceeded the rate limit
        if await self.redis_client.get(key):
            if isinstance(event, types.Message):
                await event.answer(
                    "⛔ Вы слишком часто используете бота. Пожалуйста, попробуйте позже.",
                    show_alert=True
                )
            elif isinstance(event, types.CallbackQuery):
                await event.answer(
                    "⛔ Вы слишком часто используете бота. Пожалуйста, попробуйте позже.",
                    show_alert=True
                )
            return

        else:
            # Set the rate limit for the user
            await self.redis_client.set_with_ttl(key=key, value="1", ttl=1)
            return await handler(event, data)