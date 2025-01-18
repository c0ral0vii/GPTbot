from redis.asyncio import Redis
from src.config.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


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

    async def set_hset(self, key: str, **kwargs):
        """Установка hset"""
        try:
            await self.redis.hset(key, mapping={**kwargs})
        except Exception as e:
            logger.error(e)

    async def get_hgetall(self, key: str):
        return await self.redis.hgetall(key)

    async def set(self, key: str, value: str):
        """Установка set"""
        try:
            await self.redis.set(name=key, value=value)
        except Exception as e:
            logger.error(e)

    async def delete(self, key: str):
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(e)
            return


redis_manager = RedisCache()
