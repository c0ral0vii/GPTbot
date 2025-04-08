import asyncio
from typing import Dict, Any
import json

import aiohttp
from anthropic import AsyncAnthropic

from src.config.config import settings
from src.db.enums_class import MessageRole
from src.db.orm.user_orm import UserORM
from src.scripts.answer_messages.answer_message import AnswerMessage
from src.scripts.dialog.service import DialogService
from src.scripts.energy_remover.service import EnergyService
from src.utils.logger import setup_logger


class ClaudeGPT:
    def __init__(self):
        self.API_KEY = settings.MJ_KEY
        self.message_client = AnswerMessage()
        self.energy_service = EnergyService()
        self.dialog_service = DialogService()

        self.logger = setup_logger(__name__)
        self.HEADER = {
            "Content-Type": "application/json",
            "Authorization": self.API_KEY,
        }
        self.timeout = [
            30,
        ]

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

    async def send_message(self, data: Dict[str, Any]):
        """Отправка сообщения"""

        api_link = "https://api.goapi.ai/v1/chat/completions"
        
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

            message = json.dumps(
                {
                    "model": data["version"],
                    "messages": import_messages,
                    "max_tokens": 4096,
                }
            ).encode("utf-8")
            
            self.logger.debug(message)
            
            max_retries = 5
            retry_count = 0
            retry_delay = 5
            
            for attempt in range(3):
                async with aiohttp.ClientSession() as session:
                    response = await session.post(
                        api_link,
                        headers=self.HEADER,
                        data=message,
                    )
           
                    if response.status == 200:
                        text_only = message_answer["choices"][0]["message"]["content"]
                        self.logger.debug(text_only)
                        
                        await self.dialog_service.add_message(
                            role=MessageRole.ASSISTANT,
                            dialog_id=data["dialog_id"],
                            message=text_only,
                        )

                        data["text"] = text_only
                        await self.message_client.answer_message(data)
                        return
                    
                    elif response.status in [503, 524]:
                        if retry_count < max_retries - 1:
                            await asyncio.sleep(retry_delay * (attempt + 1))
                            continue
                        
                        else:
                            self.logger.error(f"Ошибка загрузки: {response.status}-{response}")
                            data["text"] = "Произошла ошибка, обратитесь в поддержку"
                            await self.message_client.answer_message(data)
                            return
                        
                    message_answer = await response.json()
                    self.logger.debug(message_answer)
                

            # text_only = message_answer["choices"][0]["message"]["content"]
            # self.logger.debug(text_only)
            
            # await self.dialog_service.add_message(
            #     role=MessageRole.ASSISTANT,
            #     dialog_id=data["dialog_id"],
            #     message=text_only,
            # )

            # data["text"] = text_only
            # await self.message_client.answer_message(data)

        except Exception as e:
            await UserORM.add_energy(data["user_id"], data["energy_cost"])
            self.logger.error(f"Failed to send message: {e}")
            data["text"] = (
                f"Произошла ошибка, обратитесь в поддержку с данной ошибкой: \n\n{str(e)}"
            )
            await self.message_client.answer_message(data)
            raise
