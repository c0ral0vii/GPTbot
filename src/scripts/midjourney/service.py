import asyncio
import json
import io

from typing import Dict, Any
from PIL import Image
from aiogoogletrans import Translator
import aiohttp
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.config.config import settings
from src.utils.logger import setup_logger
from src.scripts.answer_messages.answer_message import AnswerMessage
from src.db.orm.user_orm import ImageORM


logger = setup_logger(__name__)


class TranslateService:
    def __init__(self):
        self.language = "en"
        self.translator = Translator()

    async def _check_to_prompt(self, text: str) -> list[str]:
        """Убираем лишние -- и одиночные тире"""

        try:
            text = text.replace("——", "--")
            split_text = text.split("--")
            return split_text
        except Exception as e:
            logger.error(e)
            return []

    async def _collect_text(self, list_text: list[str]) -> str:
        """Собираем текст"""

        try:
            collect_text = " --".join(list_text)
            logger.debug(list_text)
            return collect_text
        except Exception as e:
            logger.error(e)
            return ""

    async def translate(self, text: str) -> str:
        """Переводим текст"""
        try:
            text_translate = await self._check_to_prompt(text)
            if not text_translate:
                return text

            logger.debug(text_translate)

            translation = await self.translator.translate(
                text_translate[0], dest=self.language
            )
            text_translate[0] = translation.text.replace("—", "").replace("-", "")

            collect_text = await self._collect_text(text_translate)
            logger.debug(translation.text)
            
            # Обрабатываем тире в переведенном тексте

            return collect_text
        except Exception as e:
            logger.error(e)
            return text


class MidjourneyService:
    def __init__(self):
        self.API_KEY = settings.MJ_KEY
        self.BASE_URL = "https://api.goapi.ai"
        self.message_handler = AnswerMessage()
        self.translator = TranslateService()

        self.HEADER = {
            "Content-Type": "application/json",
            "x-api-key": self.API_KEY,
        }

    async def generate_photo(self, body: Dict[str, Any]):
        generate_url = self.BASE_URL + "/api/v1/task"

        async with aiohttp.ClientSession() as session:
            try:
                translate_message = await self.translator.translate(body["message"])
                logger.debug(translate_message)
                body["message"] = translate_message
                mode = body.get("speed_mode", "relax")
                data = json.dumps(
                    {
                        "model": "midjourney",
                        "task_type": "imagine",
                        "input": {
                            "prompt": f"{body["message"]}",
                            "process_mode": mode,
                            "skip_prompt_check": False,
                            "bot_id": 0,
                        },
                        "config": {
                            "service_mode": "",
                            "webhook_config": {"endpoint": "", "secret": ""},
                        },
                    }
                ).encode()

                result = await session.post(
                    generate_url, headers=self.HEADER, data=data
                )

                if result.status == 200:
                    response = await result.json()
                    if response.get("code") == 200:
                        body["hash"] = response["data"]["task_id"]
                        logger.debug(body)

                        await self._check_status(body=body, session=session)

                else:
                    await self.message_handler.answer_message(data=body)

            except Exception as e:
                logger.error(e)
                raise

    async def _check_status(
        self,
        body: Dict[str, Any],
        session: aiohttp.ClientSession,
        max_retries: int = 20,
        initial_delay: float = 2.0,
        backoff_factor: float = 1.5,
    ) -> None:
        """
        Проверяет статус задачи с экспоненциальной задержкой между попытками

        Args:
            body: Словарь с данными запроса
            session: aiohttp сессия
            max_retries: Максимальное количество попыток
            initial_delay: Начальная задержка между попытками (в секундах)
            backoff_factor: Множитель для экспоненциальной задержки
        """
        retry_count = 0
        current_delay = initial_delay

        while retry_count < max_retries:
            try:
                check_url = f"{self.BASE_URL}/api/v1/task/{body['hash']}"
                result = await session.get(check_url, headers=self.HEADER)
                response = await result.json()
                status = response.get("data", {}).get("status")

                if not status:
                    logger.warning(
                        f"No status received, retrying... (attempt {retry_count + 1})"
                    )
                    retry_count += 1
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor
                    continue

                if status == "completed":
                    body["original_link"] = response["data"]["output"]["image_url"]
                    body["photo"] = await self._resize_image(body["original_link"])

                    if not body.get("image_id"):
                        image = await ImageORM.create_image(
                            prompt=body["message"],
                            hash=body["hash"],
                            first_hash=body["hash"],
                            image_name=body["original_link"],
                        )
                        body["image_id"] = image.id
                    else:
                        await ImageORM.change_image_hash(
                            image_id=body["image_id"],
                            hash=body["hash"],
                        )

                    await self.message_handler.answer_photo(data=body)
                    await session.close()
                    return

                elif status == "failed":
                    logger.error(f"Task failed: {response}")
                    if retry_count >= 4:
                        await session.close()
                        
                        logger.warning("Max retries reached for failed status")
                        await self.message_handler.answer_message(data=body)
                        return

                    retry_after = response.get("retry_after", current_delay)
                    logger.warning(f"Retrying after {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                    retry_count += 1
                    current_delay *= backoff_factor
                    continue

                else:  # pending or other statuses
                    logger.debug(f"Task status: {status}, waiting...")
                    await asyncio.sleep(current_delay)
                    retry_count += 1
                    current_delay *= backoff_factor

            except aiohttp.ClientError as e:
                logger.warning(
                    f"Network error: {e}, retrying... (attempt {retry_count + 1})"
                )
                retry_count += 1
                await asyncio.sleep(current_delay)
                current_delay *= backoff_factor

            except Exception as e:
                await session.close()

                logger.error(f"Unexpected error: {e}")
                await self.message_handler.answer_message(data=body)
                return

    async def refresh_generate(self, body: Dict[str, Any]):
        """Повторная генерация"""

        reroll_url = self.BASE_URL + "/api/v1/task"
        image_data = await ImageORM.get_image(id=body["image_id"])
        body["message"] = image_data.prompt

        async with aiohttp.ClientSession() as session:
            try:
                data = json.dumps(
                    {
                        "model": "midjourney",
                        "task_type": "reroll",
                        "input": {
                            "origin_task_id": f"{image_data.first_hash}",
                            "prompt": image_data.prompt,
                            "skip_prompt_check": False,
                        },
                        "config": {
                            "service_mode": "",
                            "webhook_config": {"endpoint": "", "secret": ""},
                        },
                    },
                ).encode()

                result = await session.post(
                    reroll_url,
                    headers=self.HEADER,
                    data=data,
                )

                logger.debug(result.status)

                if result.status == 200:
                    response = await result.json()
                    if response.get("code") == 200:
                        body["hash"] = response["data"]["task_id"]
                        logger.debug(body)

                        await self._check_status(body=body, session=session)
                else:
                    logger.debug(body)
                    await self.message_handler.answer_message(data=body)

            except Exception as e:
                logger.error(e)
                raise

    async def upscale_photo(self, body: Dict[str, Any]):
        """Выбрать одно фото"""

        upscale_url = self.BASE_URL + "/api/v1/task"
        image_data = await ImageORM.get_image(id=body["image_id"])
        body["message"] = image_data.prompt

        async with aiohttp.ClientSession() as session:
            try:
                data = json.dumps(
                    {
                        "model": "midjourney",
                        "task_type": "upscale",
                        "input": {
                            "origin_task_id": image_data.hash,
                            "index": f"{body["choice"]}",
                        },
                        "config": {
                            "service_mode": "",
                            "webhook_config": {"endpoint": "", "secret": ""},
                        },
                    }
                ).encode()

                result = await session.post(
                    upscale_url,
                    headers=self.HEADER,
                    data=data,
                )

                logger.debug(result.status)

                if result.status == 200:
                    response = await result.json()
                    if response.get("code") == 200:
                        body["hash"] = response["data"]["task_id"]

                        body["keyboard"] = InlineKeyboardMarkup(
                            inline_keyboard=[
                                [
                                    InlineKeyboardButton(
                                        text="🔄",
                                        callback_data=f"refresh_{body["image_id"]}",
                                    )
                                ],
                                [
                                    InlineKeyboardButton(
                                        text="❌ Отмена", callback_data="cancel"
                                    )
                                ],
                            ]
                        )
                        await self._check_status(body=body, session=session)
                else:
                    logger.debug(body)
                    await self.message_handler.answer_message(data=body)

            except Exception as e:
                logger.error(e)
                raise

    async def vary_photo(self, body: Dict[str, Any]):
        """Создать вариации одной фотографии"""

        upscale_url = self.BASE_URL + "/api/v1/task"
        image_data = await ImageORM.get_image(id=body["image_id"])
        body["message"] = image_data.prompt

        async with aiohttp.ClientSession() as session:
            try:
                data = json.dumps(
                    {
                        "model": "midjourney",
                        "task_type": "variation",
                        "input": {
                            "origin_task_id": image_data.hash,
                            "index": f"{body["choice"]}",
                            "prompt": image_data.prompt,
                            "skip_prompt_check": False,
                        },
                        "config": {
                            "service_mode": "",
                            "webhook_config": {"endpoint": "", "secret": ""},
                        },
                    }
                ).encode()

                result = await session.post(
                    upscale_url,
                    headers=self.HEADER,
                    data=data,
                )

                logger.debug(result.status)

                if result.status == 200:
                    response = await result.json()
                    if response.get("code") == 200:
                        body["hash"] = response["data"]["task_id"]

                        await self._check_status(body=body, session=session)
                else:
                    await self.message_handler.answer_message(data=body)

            except Exception as e:
                logger.error(e)
                raise

    async def _resize_image(
        self, url: str, max_size: int = 5500000, target_width: int = 800
    ):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.read()
                        image = Image.open(io.BytesIO(data))

                        original_size = len(data)
                        if original_size > max_size:
                            ratio = target_width / image.width
                            new_height = int(image.height * ratio)
                            resized_image = image.resize((target_width, new_height))

                            buffer = io.BytesIO()
                            resized_image.save(buffer, format="JPEG", quality=85)
                            buffer.seek(0)

                            return buffer.getvalue()
                        else:
                            logger.info(
                                "Image size is within limits, no resizing needed."
                            )
                            return data
                    else:
                        logger.error(f"Failed to fetch image: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error while resizing image: {e}")
            raise
