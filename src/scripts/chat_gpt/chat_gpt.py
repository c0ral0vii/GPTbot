import io
from typing import Dict, Any

import aiohttp
from openai import AsyncOpenAI
import asyncio

from src.config.config import settings
from src.scripts.answer_messages.answer_message import AnswerMessage
from src.scripts.dialog.service import DialogService
from src.scripts.energy_remover.service import EnergyService
from src.db.enums_class import MessageRole

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

                    raw_data = await response.read()

                    try:
                        return raw_data.decode("utf-8")
                    except UnicodeDecodeError:
                        for encoding in [
                            "windows-1251",
                            "cp1251",
                            "iso-8859-1",
                            "koi8-r",
                        ]:
                            try:
                                return raw_data.decode(encoding)
                            except UnicodeDecodeError:
                                continue

                        self.logger.warning(
                            "Не удалось определить кодировку, используется замена ошибок"
                        )
                        return raw_data.decode("utf-8", errors="replace")

        except Exception as e:
            self.logger.error(e)
            return ""

    async def transcribe_audio(self, path_to_file: str) -> str:
        """Отправка голосового файла в Whisper и получение текста"""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(path_to_file) as response:
                    if response.status != 200:
                        self.logger.error(
                            f"Ошибка загрузки файла для транскрипции: {response.status}"
                        )
                        return "Оповести пользователя о том, что произошла ошибка при транскрибации, предложи ему отправить снова его голосовое сообщение"

                    audio_bytes = await response.read()

                    audio_file = io.BytesIO(audio_bytes)
                    audio_file.name = "voice.ogg"

                    transcription = await self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                    )
                    return transcription.text
        except Exception as e:
            self.logger.error(f"Ошибка транскрипции: {e}")
            return "Оповести пользователя о том, что произошла ошибка при транскрибации, предложи ему отправить снова его голосовое сообщение"

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
            file = data.get("file")

            if message and len(message) >= 1:
                await self.dialog_service.add_message(
                    role=MessageRole.USER,
                    dialog_id=data["dialog_id"],
                    message=data.get("message"),
                )

            if file:
                if file["type"] == "voice":
                    content = await self.transcribe_audio(path_to_file=file["url"])
                if file["type"] == "document":
                    content = await self._file_generate(path_to_file=file["url"])

                await self.dialog_service.add_message(
                    role=MessageRole.USER,
                    dialog_id=data["dialog_id"],
                    message=content,
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
                text_only = message_response.data[0].content[0].text.value
                await self.dialog_service.add_message(
                    role=MessageRole.ASSISTANT,
                    dialog_id=data["dialog_id"],
                    message=text_only,
                )
                
            data["text"] = text_only
            await self.message_client.answer_message(data)

        except Exception as e:
            self.logger.debug(e)
            data["text"] = f"Произошла ошибка, обратитесь в поддержку с данной ошибкой"
            await self.message_client.answer_message(data)
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
            if message and len(message) >= 1:
                await self.dialog_service.add_message(
                    role=MessageRole.USER,
                    dialog_id=data["dialog_id"],
                    message=data.get("message"),
                )

            file = data.get("file")
            if file:
                if file["type"] == "voice":
                    content = await self.transcribe_audio(path_to_file=file["url"])
                if file["type"] == "document":
                    content = await self._file_generate(path_to_file=file["url"])

                await self.dialog_service.add_message(
                    role=MessageRole.USER,
                    dialog_id=data["dialog_id"],
                    message=content,
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

            data["text"] = text_only
            await self.message_client.answer_message(data)

        except Exception as e:
            self.logger.error(f"Ошибка при отправке сообщения: {str(e)}")
            data["text"] = (
                f"Произошла ошибка, обратитесь в поддержку с данной ошибкой: \n\n{str(e)}"
            )
            await self.message_client.answer_message(data)
            raise
