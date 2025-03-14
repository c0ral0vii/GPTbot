from redis.asyncio import Redis
from src.config.config import settings
from src.utils.logger import setup_logger
import json

logger = setup_logger(__name__)

class RedisCache:
    def __init__(self):
        self.redis = None

    def get_redis_manager(self):
        return Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASS,
                db=0,
            )

    async def connect(self):
        """Создает подключение к Redis."""
        if not self.redis:
            self.redis = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASS,
                db=0,
                ssl=True,
                ssl_ca_certs="./.redis/root.crt"
            )


    async def close(self):
        """Закрывает соединение с Redis."""
        if self.redis:
            await self.redis.close()
            self.redis = None

    async def get(self, key: str) -> dict | None:
        await self.connect()
        data = await self.redis.get(key) if self.redis else None
        return json.loads(data) if data else None

    async def set(self, key: str, value: dict, ttl: int = None):
        """Объединенный метод для set и set_with_ttl."""
        try:
            await self.connect()
            data = json.dumps(value)
            return await self.redis.set(name=key, value=data, ex=ttl) if self.redis else False
        except Exception as e:
            logger.error(f"Redis в режиме только для чтения! Не удалось записать данные.. {e}")
            return False

    async def set_hset(self, key: str, **kwargs):
        """Установка hset."""
        try:
            await self.connect()
            if self.redis:
                await self.redis.hset(key, mapping=kwargs)
        except Exception as e:
            logger.error(e)

    async def get_hgetall(self, key: str):
        await self.connect()
        return await self.redis.hgetall(key) if self.redis else None

    async def delete(self, key: str):
        try:
            await self.connect()
            if self.redis:
                await self.redis.delete(key)
        except Exception as e:
            logger.error(e)

    async def update_cache(self, key: str, data: dict, ttl: int = 300):
        """Обновляет кеш при изменении данных."""
        await self.set(key, data, ttl)


redis_manager = RedisCache()
