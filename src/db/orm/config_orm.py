from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.custom_decorators import with_session
from src.db.database import async_session
from src.db.models import User, UserConfig
from src.db.enums_class import GPTConfig, CLAUDEConfig, MidjourneySpeedConfig


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
        user_id: int,
        change_setting: GPTConfig | CLAUDEConfig | MidjourneySpeedConfig = None,
        auto_renewal: bool = None,
    ) -> Optional[UserConfig]:
        async with async_session() as session:
            stmt = select(UserConfig).where(UserConfig.user_id == user_id)
            result = await session.execute(stmt)
            user_config = result.scalar_one_or_none()

            if user_config is None:
                user_config = await ConfigORM.create_config(user_id)

            if auto_renewal:
                if user_config.auto_renewal is True:
                    user_config.auto_renewal = False
                else:
                    user_config.auto_renewal = True

            if change_setting:
                if isinstance(change_setting, GPTConfig):
                    user_config.gpt_select = change_setting
                if isinstance(change_setting, CLAUDEConfig):
                    user_config.claude_select = change_setting
                if isinstance(change_setting, MidjourneySpeedConfig):
                    user_config.midjourney_speed = change_setting

            await session.commit()

            return user_config

    @staticmethod
    @with_session
    async def get_config(
        user_id: int, session: AsyncSession = None
    ) -> Optional[UserConfig]:
        stmt = select(UserConfig).where(UserConfig.user_id == user_id)
        result = await session.execute(stmt)
        user_config = result.scalar_one_or_none()

        if user_config is None:
            return None
        return user_config

    @staticmethod
    @with_session
    async def get_all_auto_sub_users(session: AsyncSession = None):
        stmt = select(UserConfig).where(UserConfig.auto_renewal == True)
        result = await session.execute(stmt)
        users = result.scalars().all()

        return users
