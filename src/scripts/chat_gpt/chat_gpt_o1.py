from typing import Dict, Any
from openai import AsyncOpenAI
import asyncio

from src.config.config import settings
from src.scripts.answer_messages.answer_message import AnswerMessage
from src.utils.logger import setup_logger


class ChatGPT:
    def __init__(self):
        self.API_KEY = settings.GPT_KEY
        self.message_client = AnswerMessage()
        self.client = AsyncOpenAI(api_key=self.API_KEY)
        self.logger = setup_logger(__name__)

        self.timeout = [
            30,
        ]

    async def send_message(self, data: Dict[str, Any]):
        """Отправка сообщения и возврат текстового ответа."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": data["message"],
                    }
                ],
                max_tokens=1024,
            )

            text_only = response.choices[0].message.content
            data["text"] = text_only

            await self.message_client.answer_message(data)

        except Exception as e:
            self.logger.error(f"Ошибка при отправке сообщения: {e}")
            await self.message_client.answer_message(data)
            raise