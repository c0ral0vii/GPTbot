from typing import Dict, Any

import aiohttp
from yookassa import Configuration, Payment
from yookassa.domain.models import Currency
from yookassa.domain.request import PaymentRequestBuilder
import uuid

from src.config.config import settings
from src.utils.logger import setup_logger


class PaymentService:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.API_KEY = settings.YOOMONEY_API

        self.API_ENDPOINT = "https://api.yookassa.ru/v3/"

        Configuration.configure("1020161", self.API_KEY)

    async def generate_yookassa_link(self, user_id: int) -> Dict[str, Any]:
        """Генерация ссылки на покупку"""

        payment = Payment.create(
            {
                "amount": {
                    "value": 990,
                    "currency": "RUB",
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "https://yookassa.ru",
                },
                "metadata": {
                    "user_id": user_id,
                },
                "capture": True,
                "description": "Покупка премиума на 1 месяц",
            },
            uuid.uuid4(),
        )

        self.logger.debug(payment.json())
        return payment.confirmation.confirmation_url


    async def generate_prodamus_link(self, user_id: int) -> Dict[str, Any]:
        """Генеоация ссылки продамус"""