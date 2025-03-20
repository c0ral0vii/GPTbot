import io
import os
import traceback
from typing import Dict, Any, Coroutine

import aiohttp
from openai import AsyncOpenAI
import asyncio

from openai.types import FileObject
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

    async def _file_generate(self, path_to_file: str) -> str:
        """Создание файла для OpenAI из удалённой ссылки"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(path_to_file) as response:
                    if response.status != 200:
                        self.logger.error(f"Ошибка загрузки: {response.status}")
                        return ""

                    file_content = await response.text()
                    return file_content
        except Exception as e:
            self.logger.error(e)

    async def send_message_assistant(self, data):
        try:
            status = await self.energy_service.upload_energy(data, "remove")
            if isinstance(status, dict):
                data["energy_text"] = None
                await self.message_client.answer_message(data)
                return

            self.logger.debug(data)
            data["energy_text"] = status

            message = data.get("message")
            if message:
                await self.dialog_service.add_message(
                    role=MessageRole.USER,
                    dialog_id=data["dialog_id"],
                    message=data.get("message"),
                )

            file = data.get("file")
            if file:
                content_file = await self._file_generate(path_to_file=file["url"])
                await self.dialog_service.add_message(
                    role=MessageRole.USER,
                    dialog_id=data["dialog_id"],
                    message=content_file,
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
                max_prompt_tokens=25000,
                max_completion_tokens=8000,
            )

            while run.status != "completed":
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id, run_id=run.id
                )
                await asyncio.sleep(2.5)
            else:
                message_response = await self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                text_only = message_response.data[0].content[0].text.value[:4096]

            chunk_size = 4000
            chunks = [
                text_only[i : i + chunk_size]
                for i in range(0, len(text_only), chunk_size)
            ]

            data["text"] = chunks
            data["disable_delete"] = True
            for chunk in chunks:
                data["text"] = chunk
                await self.message_client.answer_message(data)
                data["disable_delete"] = False

        except Exception as e:
            self.logger.debug(e)
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

            message = data.get("message")
            if message:
                await self.dialog_service.add_message(
                    role=MessageRole.USER,
                    dialog_id=data["dialog_id"],
                    message=data.get("message"),
                )

            file = data.get("file")
            if file:
                content_file = await self._file_generate(path_to_file=file["url"])
                await self.dialog_service.add_message(
                    role=MessageRole.USER,
                    dialog_id=data["dialog_id"],
                    message=content_file,
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
                max_completion_tokens=4096,
            )

            text_only = response.choices[0].message.content
            await self.dialog_service.add_message(
                role=MessageRole.ASSISTANT,
                dialog_id=data["dialog_id"],
                message=text_only,
            )

            chunk_size = 4000
            chunks = [
                text_only[i : i + chunk_size]
                for i in range(0, len(text_only), chunk_size)
            ]

            data["text"] = chunks
            data["disable_delete"] = True

            for chunk in chunks:
                data["text"] = chunk
                await self.message_client.answer_message(data)
                data["disable_delete"] = False

        except Exception as e:
            self.logger.error(f"Ошибка при отправке сообщения: {str(e)}")
            # await self.message_client.answer_message(data)
            raise
