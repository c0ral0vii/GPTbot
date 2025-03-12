from typing import Dict, Any

import uuid
from yookassa import Configuration, Payment

from src.config.config import settings
from src.utils.logger import setup_logger


class PaymentService:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.API_KEY = settings.YOOMONEY_API

        self.API_ENDPOINT = "https://api.yookassa.ru/v3/"

        Configuration.configure("1013385", self.API_KEY)

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
                "receipt": {
                    "customer": {
                        "email": "metlinahelen@yandex.ru",
                        "phone": "79119118595",
                    },
                "items": [
                        {
                            "description": "Премиум подписка",
                            "quantity": 1.000,
                            "amount": {
                                "value": "990.00",
                                "currency": "RUB"
                            },
                            "vat_code": 4,
                            "payment_mode": "full_payment",
                            "payment_subject": "service"
                        }
                    ]
                }
            },
            uuid.uuid4(),
        )

        self.logger.debug(payment.json())
        return payment.confirmation.confirmation_url
