import pathlib

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_PATH = pathlib.Path(__file__).parent.parent.parent.parent
EXCLUDE_PATTERN = r"^(?!/.*|💡 Chat GPT/Claude$|🧑‍🔬 Ассистенты).+"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    # bot_api
    BOT_API: str
    # db
    DB_HOST: str = "db"
    DB_NAME: str = "gpt_db"
    DB_USER: str = "root"
    DB_PASS: str = "root"
    DB_PORT: int = 5432
    # redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASS: str = "root"
    # rabbit
    RABBIT_USER: str = "guest"
    RABBIT_PASS: str = "guest"
    RABBIT_HOST: str = "rabbitmq"
    RABBIT_PORT: int = 5672

    # text / code
    GPT_KEY: str = None
    CLAUDE_KEY: str = None
    GPT_ASSIS_KEY: str = None
    # image
    MJ_KEY: str = None
    FLUX_KEY: str = None
    DALL_KEY: str = None
    # YOOMONEY_API
    YOOMONEY_API: str = None
    SHOP_ID: str = None

    # admin token
    ADMIN_TOKEN: str = None
    ADMIN_USER: str = "root"
    ADMIN_PASS: str = "root"

    # debug
    DEBUG: bool = False

    @property
    def TEXT_GPT(self):
        return {
            "gpt-4o-mini": {
                "energy_cost": 10,
                "select_model": "ChatGPT 4o-mini",
                "premium_free": True,
                "file_use": True,
                "voice": True,
            },
            "gpt-4o": {
                "energy_cost": 10,
                "select_model": "ChatGPT 4o",
                "premium_free": True,
                "file_use": True,
                "voice": True,
            },
            "o1": {
                "energy_cost": 10,
                "select_model": "ChatGPT o1",
                "premium_free": True,
                "file_use": True,
                "voice": True,
            },
            "gpt-4.5-preview": {
                "energy_cost": 10,
                "select_model": "ChatGPT 4.5",
                "premium_free": True,
                "file_use": True,
                "voice": True,
                "disable": True,
            },
            "claude-3-5-haiku-latest": {
                "energy_cost": 10,
                "select_model": "Claude 3.5 Haiku",
                "premium_free": True,
                "file_use": True,
                "voice": False,
            },
            "claude-3-5-sonnet-latest": {
                "energy_cost": 10,
                "select_model": "Claude 3.5 Sonnet",
                "premium_free": True,
                "file_use": True,
                "voice": False,
            },
        }

    @property
    def IMAGE_GPT(self):
        return {
            "midjourney": {
                "energy_cost": 10,
                "select_model": "Midjourney",
                "premium_free": False,
            }
        }

    @property
    def bot_api(self) -> str:
        return self.BOT_API

    @property
    def get_debug_settings(self):
        return self.DEBUG

    @property
    def get_claude_key(self):
        return self.CLAUDE_KEY

    @property
    def get_reddis_link(self):
        return f"redis://{self.REDDIS_PASS}@{self.REDDIS_HOST}:{self.REDDIS_PORT}"

    @property
    def get_rabbit_link(self):
        return f"amqp://{self.RABBIT_USER}:{self.RABBIT_PASS}@{self.RABBIT_HOST}:{self.RABBIT_PORT}"

    @property
    def get_database_link(self):
        return rf"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
