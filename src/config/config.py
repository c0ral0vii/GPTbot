from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_API: str

    DB_HOST: str
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_PORT: int

    REDDIS_HOST: str
    REDDIS_PORT: int
    REDDIS_PASS: str

    # text / code
    GPT_KEY: str = None
    CLAUDE_KEY: str = None
    GPT_ASSIS_KEY: str = None
    # image
    MJ_KEY: str = None
    FLUX_KEY: str = None
    DALL_KEY: str = None

    DEBUG: bool

    @property
    def bot_api(self) -> str:
        return self.BOT_API


    @property
    def get_debug_settings(self):
        return self.DEBUG

    @property
    def get_claude_key(self):
        return self.CLAUDE_KEY

settings = Settings()
