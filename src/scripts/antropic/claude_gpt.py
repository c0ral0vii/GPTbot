from anthropic import AsyncAnthropic
import asyncio
import os

from src.config.config import settings

class ClaudeUse:
    def __init__(self):
        self.API_KEY = settings.get_claude_key
        self.client = AsyncAnthropic(api_key=self.API_KEY)

        self.timeout = [30,]


    async def send_message(self):
        """Отправка сообщения"""

        ...