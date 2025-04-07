from typing import Dict, Any

import uuid
from yookassa import Configuration, Payment

from src.config.config import settings
from src.utils.logger import setup_logger
from src.db.orm.config_orm import ConfigORM


class PaymentService:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.API_KEY = settings.YOOMONEY_API
        self.SHOP_ID = settings.SHOP_ID

        self.API_ENDPOINT = "https://api.yookassa.ru/v3/"

        Configuration.configure(self.SHOP_ID, self.API_KEY)

    async def generate_yookassa_link(self, user_id: int, value: int = 1490) -> Dict[str, Any]:
        """Генерация ссылки на покупку"""

        payment = Payment.create(
            {
                "amount": {
                    "value": value,
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
                "save_payment_method": True,
                "receipt": {
                    "customer": {
                        "email": "metlinahelen@yandex.ru",
                        "phone": "79119118595",
                    },
                    "items": [
                        {
                            "description": "Премиум подписка",
                            "quantity": 1.000,
                            "amount": {"value": "1490.00", "currency": "RUB"},
                            "vat_code": 4,
                            "payment_mode": "full_payment",
                            "payment_subject": "service",
                        }
                    ],
                },
            },
            uuid.uuid4(),
        )

        self.logger.debug(payment.json())
        return payment.confirmation.confirmation_url

    async def auto_pay(self, user_id: int, payment_method_id: str, value: int = 1490):
        """Автосписание"""

        self.logger.debug(payment_method_id)
        try:
            payment = Payment.create(
                {
                    "amount": {
                        "value": value,
                        "currency": "RUB",
                    },
                    "metadata": {
                        "user_id": user_id,
                    },
                    "payment_method_id": payment_method_id,
                    "capture": True,
                    "description": "Покупка премиума на 1 месяц",
                    "save_payment_method": True,
                    "receipt": {
                        "customer": {
                            "email": "metlinahelen@yandex.ru",
                            "phone": "79119118595",
                        },
                        "items": [
                            {
                                "description": "Премиум подписка",
                                "quantity": 1.000,
                                "amount": {"value": "1490.00", "currency": "RUB"},
                                "vat_code": 4,
                                "payment_mode": "full_payment",
                                "payment_subject": "service",
                            }
                        ],
                    },
                },
                uuid.uuid4(),
            )
            self.logger.debug(payment.json())

        except Exception as e:
            await ConfigORM.change_config(user_id=user_id, auto_renewal=True)

            self.logger.error(e)
