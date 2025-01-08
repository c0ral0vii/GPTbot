from redis.asyncio import Redis
from src.config.config import settings


class RedisCache:
    def __init__(self):
        self.redis = Redis()


redis_manager = RedisCache()