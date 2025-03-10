import json
from typing import Dict, Any

import aiohttp
import uuid

from src.config.config import settings
from src.utils.logger import setup_logger


class PaymentService:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.PRODAMUS_API = settings.PRODAMUS_API

        self.API_ENDPOINT = "https://gradov.payform.ru/"

    async def generate_prodamus_payment_link(self, user_id: int):
        """Генерация ссылки на оплату подписки от продамуса"""

        data = {
            "do": "link",
             "products": [
                {
                    "name": "Подписка бота на 1 месяц",
                    "price": 990,
                    "quantity": 1,
                }
            ],
            "type": "json",
            "callbackType": "json",
            "currency": "rub",
            "payments_limit": 1,
            "order_id": 1,
            "paid_content": "Спасибо за покупку!",
            "sys": "",
        }

        data["signature"] = self._create_hmac_signature(data, self.PRODAMUS_API)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    self.API_ENDPOINT,
                    json=data,
                    headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    text = await response.text()
                    self.logger.info(text)
                    response_data = await response.json()
                    return response_data.get("url")  # Возвращаем ссылку на оплату
                else:
                    self.logger.error(f"Ошибка при генерации ссылки: {response.status}")
                    raise Exception("Не удалось создать платежную ссылку")

    def _create_hmac_signature(self, data: Dict[str, Any], secret_key: str) -> str:
        """Создает HMAC-подпись для данных."""
        import hmac
        import hashlib

        # Сортируем данные по ключам
        sorted_data = sorted(data.items(), key=lambda x: x[0])

        # Преобразуем данные в строку
        data_string = "&".join([f"{key}={value}" for key, value in sorted_data])

        # Создаем HMAC-подпись с использованием SHA-256
        signature = hmac.new(
            secret_key.encode("utf-8"),
            data_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return signature
