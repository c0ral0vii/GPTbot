from typing import Any
from src.utils.generate_payment import PaymentService


class ReccurentPay:
    def __init__(self):
        self.pay_service = PaymentService()
        
    
    async def check_autopay():
        """Проверка кому нужно продлить подписку"""
        
        ...
        
    async def _autopay(self, user_id: int, count_pay: int, renewal_id: str) -> dict[str, Any]:
        """Продление подписки пользователям"""
        
        ...