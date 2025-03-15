from typing import Dict, Any
from openai import AsyncOpenAI
import asyncio

from src.config.config import settings
from src.db.models import Message
from src.db.orm.dialog_orm import DialogORM
from src.db.orm.user_orm import UserORM
from src.scripts.answer_messages.answer_message import AnswerMessage
from src.scripts.dialog.service import DialogService
from src.scripts.energy_remover.service import EnergyService
from src.db.enums_class import MessageRole, GPTConfig

from src.utils.logger import setup_logger


class ChatGPT:
    def __init__(self):
        self.API_KEY = settings.GPT_KEY
        self.message_client = AnswerMessage()
        self.energy_service = EnergyService()
        self.dialog_service = DialogService()

        self.client = AsyncOpenAI(api_key=self.API_KEY, max_retries=5)
        self.logger = setup_logger(__name__)

        self.timeout = [
            30,
        ]

    async def get_gpt_assistant(self, assistant_id: str):
        assistant = await self.client.beta.assistants.retrieve(
            assistant_id=assistant_id,
        )


    async def send_message(self, data: Dict[str, Any]):
        """Отправка сообщения и возврат текстового ответа."""
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

            response = await self.client.chat.completions.create(
                model=data["version"],
                messages=import_messages,
                max_tokens=3000,
            )

            text_only = response.choices[0].message.content
            await self.dialog_service.add_message(
                role=MessageRole.ASSISTANT,
                dialog_id=data["dialog_id"],
                message=text_only,
            )

            data["text"] = text_only

            await self.message_client.answer_message(data)

        except Exception as e:
            self.logger.error(f"Ошибка при отправке сообщения: {str(e)}")
            # await self.message_client.answer_message(data)
            raise