from typing import Dict, Any

from anthropic import AsyncAnthropic
import asyncio
import os

from src.config.config import settings
from src.db.orm.user_orm import UserORM
from src.scripts.answer_messages.answer_message import AnswerMessage
from src.utils.logger import setup_logger


class ClaudeGPT:
    def __init__(self):
        self.API_KEY = settings.get_claude_key
        self.message_client = AnswerMessage()
        self.client = AsyncAnthropic(api_key=self.API_KEY)
        self.logger = setup_logger(__name__)

        self.timeout = [
            30,
        ]

    async def send_message(self, data: Dict[str, Any]):
        """Отправка сообщения"""

        try:
            text = await UserORM.remove_energy(data["user_id"], data["energy_cost"])
            if text.get("error"):
                data["text"] = text["text"]
                data["energy_text"] = None
                await self.message_client.answer_message(data)
                return
            data["energy_text"] = text["text"]

            assistant = {
                "role": "assistant",
                "content": data.get(
                    "last_message",
                    "Ты пока ничего не писал, считай это сообщение пустым",
                ),
            }
            messages = [
                assistant,
                {
                    "role": "user",
                    "content": data["message"],
                },
            ]

            message = await self.client.messages.create(
                max_tokens=1024,
                messages=messages,
                model="claude-3-5-sonnet-latest",
            )

            self.logger.debug(message.content)
            data["text"] = " ".join(
                [block.text for block in message.content if block.type == "text"]
            )

            await self.message_client.answer_message(data)

        except Exception as e:
            await UserORM.add_energy(data["user_id"], data["energy_cost"])
            self.logger.error(f"Failed to send message: {e}")
            # await self.message_client.answer_message(data)
            raise
