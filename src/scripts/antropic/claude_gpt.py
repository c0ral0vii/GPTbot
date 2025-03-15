from typing import Dict, Any

from anthropic import AsyncAnthropic
import asyncio
import os

from src.config.config import settings
from src.db.enums_class import MessageRole
from src.db.orm.user_orm import UserORM
from src.scripts.answer_messages.answer_message import AnswerMessage
from src.scripts.dialog.service import DialogService
from src.scripts.energy_remover.service import EnergyService
from src.utils.logger import setup_logger


class ClaudeGPT:
    def __init__(self):
        self.API_KEY = settings.get_claude_key
        self.message_client = AnswerMessage()
        self.energy_service = EnergyService()
        self.dialog_service = DialogService()

        self.client = AsyncAnthropic(api_key=self.API_KEY)
        self.logger = setup_logger(__name__)

        self.timeout = [
            30,
        ]

    async def send_message(self, data: Dict[str, Any]):
        """Отправка сообщения"""

        try:
            status = await self.energy_service.upload_energy(data, "remove")
            if isinstance(status, dict):
                data["energy_text"] = None
                await self.message_client.answer_message(data)
                return

            data["energy_text"] = status

            await self.dialog_service.add_message(
                role=MessageRole.USER,
                dialog_id=data["dialog_id"],
                message=data.get("message"),
            )
            messages = await self.dialog_service.get_messages(data["dialog_id"])

            import_messages = []
            for message in messages:
                message_data = {
                    "role": message.role.value,
                    "content": message.message,
                }

                import_messages.append(message_data)

            message = await self.client.messages.create(
                max_tokens=3000,
                messages=import_messages,
                model=data["version"],
            )

            self.logger.debug(message.content)
            text_only = " ".join(
                [block.text for block in message.content if block.type == "text"]
            )
            await self.dialog_service.add_message(
                role=MessageRole.ASSISTANT,
                dialog_id=data["dialog_id"],
                message=text_only,
            )

            data["text"] = text_only

            await self.message_client.answer_message(data)

        except Exception as e:
            await UserORM.add_energy(data["user_id"], data["energy_cost"])
            self.logger.error(f"Failed to send message: {e}")
            # await self.message_client.answer_message(data)
            raise
