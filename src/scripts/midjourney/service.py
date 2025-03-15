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

    async def translate(self, text: str) -> str:
        translator = Translator()

        try:
            translation = await translator.translate(text, dest=self.language)

            return translation.text
        except Exception as e:
            logger.error(e)
            return text


class MidjourneyService:
    def __init__(self):
        self.API_KEY = settings.MJ_KEY
        self.BASE_URL = "https://api.userapi.ai"
        self.message_handler = AnswerMessage()
        self.translator = TranslateService()

        self.HEADER = {
            "Content-Type": "application/json",
            "api-key": self.API_KEY,
        }

    async def generate_photo(self, body: Dict[str, Any]):
        generate_url = self.BASE_URL + "/midjourney/v2/imagine"

        async with aiohttp.ClientSession() as session:
            try:
                translate_message = await self.translator.translate(body["message"])
                data = json.dumps(
                    {
                        "prompt": f"{body["message"]}",
                    }
                ).encode()

                result = await session.post(
                    generate_url, headers=self.HEADER, data=data
                )

                if result.status == 200:
                    response = await result.json()
                    body["hash"] = response["hash"]
                    logger.debug(body)

                    await self._check_status(body=body, session=session)

                else:
                    await self.message_handler.answer_message(data=body)

            except Exception as e:
                logger.error(e)
                raise

    async def _check_status(self, body: Dict[str, Any], session: aiohttp.ClientSession, retries: int = 0):
        try:
            check_url = self.BASE_URL + "/midjourney/v2/status?hash=" + body["hash"]
            result = await session.get(check_url, headers=self.HEADER)
            response = await result.json()

            if response["status"] == "error":
                logger.error(response)
                retry_after = response.get("retry_after", 5.0)
                logger.warning(f"Rate limited, retrying after {retry_after} seconds.")

                await asyncio.sleep(retry_after)
                await self._check_status(body=body, session=session)
                return

            if response["status"] == "done":
                body["original_link"] = response["result"]["url"]
                if response["result"]["size"] >= 5500000:
                    body["photo"] = await self._resize_image(
                        response["result"]["url"]
                    )

                else:
                    body["photo"] = response["result"]["url"]

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
            else:
                await asyncio.sleep(3)
                await self._check_status(body=body, session=session)

        except Exception as e:
            # if retries != 5:
            #     retries += 1
            #     await asyncio.sleep(retries)
            #     await self._check_status(body=body, session=session, retries=retries)
            #     logger.warning(f"Rate limited, retrying after {retries} seconds.")
            # else:
            logger.warning(f"Rate limited, retrying after {retries} seconds. {e}")
            raise

    async def refresh_generate(self, body: Dict[str, Any]):
        """Повторная генерация"""

        reroll_url = self.BASE_URL + "/midjourney/v2/reroll"
        image_data = await ImageORM.get_image(id=body["image_id"])
        body["message"] = image_data.prompt

        async with aiohttp.ClientSession() as session:
            try:
                data = json.dumps(
                    {
                        "hash": image_data.first_hash,
                        "prompt": image_data.prompt,
                    }
                ).encode()

                result = await session.post(
                    reroll_url,
                    headers=self.HEADER,
                    data=data,
                )

                logger.debug(result.status)

                if result.status == 200:
                    response = await result.json()
                    logger.debug(response)
                    body["hash"] = response["hash"]
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

        # Можно сделать получение настроек пользователя

        upscale_url = self.BASE_URL + "/midjourney/v2/upscale"
        image_data = await ImageORM.get_image(id=body["image_id"])
        body["message"] = image_data.prompt

        async with aiohttp.ClientSession() as session:
            try:
                data = json.dumps(
                    {
                        "hash": image_data.hash,
                        "choice": int(body["choice"]),
                        "prompt": image_data.prompt,
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
                    logger.debug(response)
                    body["hash"] = response["hash"]
                    logger.debug(body)
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

        upscale_url = self.BASE_URL + "/midjourney/v2/variation"
        image_data = await ImageORM.get_image(id=body["image_id"])
        body["message"] = image_data.prompt

        async with aiohttp.ClientSession() as session:
            try:
                data = json.dumps(
                    {
                        "hash": image_data.hash,
                        "choice": int(body["choice"]),
                        "prompt": image_data.prompt,
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
                    logger.debug(response)
                    body["hash"] = response["hash"]
                    logger.debug(body)

                    await self._check_status(body=body, session=session)
                else:
                    logger.debug(body)
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
