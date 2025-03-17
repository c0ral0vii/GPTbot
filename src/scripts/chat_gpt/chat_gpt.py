from typing import Dict, Any
from openai import AsyncOpenAI
import asyncio

from openai.types.beta.threads import Run

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

    async def _create_thread_with_messages(self, messages: list):
        """Создание thread с сообщениями"""

        try:
            thread = await self.client.beta.threads.create(
                messages=messages,
            )
            return thread
        except Exception as e:
            self.logger.error(e)
            raise

    async def send_message_assistant(self, data):
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

            thread = await self._create_thread_with_messages(import_messages)
            run = await self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=data["version"],
                max_completion_tokens=2500,
            )

            while run.status != "completed":
                run = await self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                await asyncio.sleep(2.5)
            else:
                message_response = await self.client.beta.threads.messages.list(thread_id=thread.id)
                text_answer = message_response.data[0].content[0].text.value[:4096]

            data["text"] = text_answer[:4000]

            await self.message_client.answer_message(data)
        except Exception:
            raise

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
                max_tokens=2500,
            )

            text_only = response.choices[0].message.content
            await self.dialog_service.add_message(
                role=MessageRole.ASSISTANT,
                dialog_id=data["dialog_id"],
                message=text_only,
            )

            data["text"] = text_only[:4000]

            await self.message_client.answer_message(data)

        except Exception as e:
            self.logger.error(f"Ошибка при отправке сообщения: {str(e)}")
            # await self.message_client.answer_message(data)
            raise