from aiogram import BaseMiddleware


from src.db.orm.user_orm import BannedUserORM
from src.utils.redis_cache.redis_cache import redis_manager


class BlockMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict):
        user_id = event.from_user.id

        key = f"{user_id}:block_user"

        if redis_manager.get(key):
            await event.answer(
                "⛔ Вы были заблокированы. Вам запрещено пользоваться ботом!"
            )
            return

        block_user = await BannedUserORM.check_banned_user(user_id=user_id)

        # Проверяем, является ли пользователь заблокированным
        if not block_user:
            return await handler(event, data)
        else:
            await redis_manager.set_with_ttl(key=key, value="block", ttl=300)
            await event.answer(
                "⛔ Вы были заблокированы. Вам запрещено пользоваться ботом!"
            )
            return
