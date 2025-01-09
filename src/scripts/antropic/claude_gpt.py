from typing import Dict, Any

from anthropic import AsyncAnthropic
import asyncio
import os

from src.config.config import settings
from src.utils.logger import setup_logger


class ClaudeGPT:
    def __init__(self):
        self.API_KEY = settings.get_claude_key
        self.client = AsyncAnthropic(api_key=self.API_KEY)
        self.logger = setup_logger(__name__)

        self.timeout = [
            30,
        ]

    async def send_message(self, data: Dict[str, Any]):
        """Отправка сообщения"""

        try:
            message = self.client.messages.create(
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": data["message"],
                    }
                ],
                model="claude-3-5-sonnet-latest",
            )

            return message.content

        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            raise