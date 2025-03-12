from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import async_session
from src.db.models import User, UserConfig
from src.db.enums_class import GPTConfig, CLAUDEConfig


class ConfigORM:
    @staticmethod
    async def create_config(user: str | int | User) -> Optional[UserConfig]:
        async with async_session() as session:
            if isinstance(user, (str, int)):
                user_id = int(user)
            else:
                user_id = user.user_id

            if user is None:
                return None

            config = UserConfig(
                user_id=user_id,
            )

            session.add(config)
            await session.commit()

            return config

    @staticmethod
    async def change_config(
        change_setting: GPTConfig | CLAUDEConfig, user_id: int
    ) -> Optional[UserConfig]:
        async with async_session() as session:
            stmt = select(UserConfig).where(UserConfig.user_id == user_id)
            result = await session.execute(stmt)
            user_config = result.scalar_one_or_none()

            if user_config is None:
                user_config = await ConfigORM.create_config(user_id)

            if isinstance(change_setting, GPTConfig):
                user_config.gpt_select = change_setting
            if isinstance(change_setting, CLAUDEConfig):
                user_config.claude_select = change_setting

            await session.commit()

            return user_config

    @staticmethod
    async def get_config(
        user_id: int, session: AsyncSession = None
    ) -> Optional[UserConfig]:
        if not session:
            session = async_session()

        stmt = select(UserConfig).where(UserConfig.user_id == user_id)
        result = await session.execute(stmt)
        user_config = result.scalar_one_or_none()

        if user_config is None:
            return None
        if not session:
            await session.close()

        return user_config
