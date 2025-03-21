class SpammerService:
    def __init__(self):
        ...

    async def spam(self, premium_users: bool, non_premium_users: bool, message: str, image: str = None):
        """Рассылка по пользователям"""

        ...

    async def _get_image(self):
        """Получение фотографии"""

        ...

    async def _get_users(self):
        """Получение пользователей"""

        ...