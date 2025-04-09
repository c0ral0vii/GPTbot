from aiogram import BaseMiddleware


from src.db.orm.user_orm import BannedUserORM
from src.utils.redis_cache.redis_cache import redis_manager


class BlockMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict):
        user_id = event.from_user.id

        key_banned = f"{user_id}:block_user"

        if await redis_manager.get(key_banned):
            await event.answer(
                "⛔ Вы были заблокированы. Вам запрещено пользоваться ботом!"
            )
            return

        key_unbanned = f"{user_id}:unbanned"
        
        if await redis_manager.get(key_unbanned):
            return await handler(event, data)
        
        block_user = await BannedUserORM.check_banned_user(user_id=user_id)

        if not block_user:
            await redis_manager.set(key=key_unbanned, value="unbanned", ttl=300)
            return await handler(event, data)
        else:
            await redis_manager.set(key=key_banned, value="block", ttl=300)
            await event.answer(
                "⛔ Вы были заблокированы. Вам запрещено пользоваться ботом!"
            )

            return
