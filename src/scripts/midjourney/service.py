import asyncio
import json
import io

from typing import Dict, Any
from PIL import Image
from aiogoogletrans import Translator
import aiohttp

from src.config.config import settings
from src.utils.logger import setup_logger
from src.scripts.answer_messages.answer_message import AnswerMessage


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
                        "prompt": f"{translate_message}",
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

    async def _check_status(self, body: Dict[str, Any], session: aiohttp.ClientSession):
        try:
            check_url = self.BASE_URL + "/midjourney/v2/status?hash=" + body["hash"]
            result = await session.get(check_url, headers=self.HEADER)

            if result.status == 200:
                response = await result.json()

                if response["status"] == "done":
                    body["original_link"] = response["result"]["url"]
                    if response["result"]["size"] > 5500000:
                        body["photo"] = await self._resize_image(
                            response["result"]["url"]
                        )
                    else:
                        body["photo"] = response["result"]["url"]

                    logger.debug(body)
                    logger.debug(response)

                    await self.message_handler.answer_photo(data=body)
                else:
                    await asyncio.sleep(2)
                    await self._check_status(body=body, session=session)

        except Exception as e:
            logger.error(e)
            raise

    async def refresh_generate(self, body: Dict[str, Any]):
        """Повторная генерация"""

        reroll_url = self.BASE_URL + "/midjourney/v2/reroll"

        async with aiohttp.ClientSession() as session:
            try:
                data = json.dumps(
                    {
                        "hash": f"{body['hash']}",
                    }
                ).encode()

                result = await session.post(
                    reroll_url, headers=self.HEADER, data=data,
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


    async def select_photo(self, caption: int, data: Dict[str, Any]):
        """Выбрать одно фото"""

        ...

    async def upgrade_photo(self, caption: int, data: Dict[str, Any]):
        """Улучшить одно фото"""

        ...

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

                            logger.info(
                                f"Image resized: original {original_size} bytes, resized {len(buffer.getvalue())} bytes"
                            )
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
