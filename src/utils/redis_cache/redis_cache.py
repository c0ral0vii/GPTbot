from redis.asyncio import Redis
from src.config.config import settings


class RedisCache:
    def __init__(self):
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASS,
        )

    def get_redis_manager(self):
        return self.redis

    async def get(self, key):
        return await self.redis.get(key)

    async def set_with_ttl(self, key: str, value: str, ttl):
        res = await self.redis.set(name=key, value=value, ex=ttl)

        if res is True:
            return True
        return False


redis_manager = RedisCache()
