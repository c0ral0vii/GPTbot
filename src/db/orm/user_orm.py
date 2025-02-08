from decimal import Decimal
from typing import Optional, Dict, Any

from src.db.models import User, GenerateImage
from src.utils.logger import setup_logger

from src.db.database import async_session
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError


logger = setup_logger(__name__)


class UserORM:
    @staticmethod
    async def create_user(
        user_id: int, use_referral_link: str = None
    ) -> dict[str, Any]:
        try:
            async with async_session() as session:
                stmt = select(User).where(User.user_id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if user is not None:
                    return {
                        "duplicate": True,
                    }

                async def create_referral_link():
                    import uuid

                    return str(uuid.uuid4())

                referral_link = await create_referral_link()
                if use_referral_link == referral_link:
                    user.referral_link = None
                    logger.debug("Попытка ввести свой же инвайт код")
                user = User(
                    user_id=user_id,
                    referral_link=referral_link,
                    use_referral_link=use_referral_link,
                )

                session.add(user)
                await session.commit()
                await session.refresh(user)

                return {
                    "duplicate": False,
                }
        except IntegrityError:
            return {
                "duplicate": True,
            }

        except Exception as e:
            logger.error(e)
            return

    @staticmethod
    async def get_owner_referral(referral_code: str) -> Dict[str, Any]:
        try:
            async with async_session() as session:
                stmt = select(User).where(User.referral_link == referral_code)
                result = await session.execute(stmt)
                owner = result.scalar_one_or_none()

                return {
                    "data": owner,
                    "user_id": owner.user_id,
                }

        except Exception as e:
            logger.error(e)
            raise

    @staticmethod
    async def remove_energy(user_id: int, count: int | str) -> Dict[str, Any]:
        try:
            async with async_session() as session:
                stmt = select(User).where(User.user_id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if user.energy >= count:
                    user.energy = user.energy - Decimal(count)
                else:
                    return {
                        "error": True,
                        "text": f"⚡ Недостаточно энергии, у вас осталось {float(user.energy):.1f}",
                    }

                session.add(user)
                await session.commit()
                return {
                    "error": False,
                    "text": f"Списано ⚡ {count}, у вас осталось ⚡ {float(user.energy):.1f}",
                }

        except Exception as e:
            logger.error(e)
            return {"text": "Ошибка, попробуйте еще раз"}

    @staticmethod
    async def add_energy(user_id: int, count: int | str) -> Dict[str, Any]:
        try:
            async with async_session() as session:
                stmt = select(User).where(User.user_id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                user.energy = user.energy + Decimal(count)

                session.add(user)
                await session.commit()

                return {
                    "text": f"Добавлено ⚡ {count}, теперь у вас ⚡ {float(user.energy):.1f}",
                }

        except Exception as e:
            logger.error(e)
            return {"text": "Ошибка, попробуйте еще раз"}

    @staticmethod
    async def get_referral_link(user_id: int) -> int:
        try:
            async with async_session() as session:
                stmt = select(User).where(User.user_id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                return user.referral_link

        except Exception as e:
            logger.error(e)
            raise

    @staticmethod
    async def get_count_referrals(user_id: int) -> int:
        try:
            async with async_session() as session:
                stmt = select(User).where(User.user_id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                referral_link = user.referral_link

                stmt = select(func.count()).where(
                    User.use_referral_link == referral_link
                )
                result = await session.execute(stmt)
                referrals_count = result.scalar()

                return referrals_count
        except Exception as e:
            logger.error(e)
            raise

    @staticmethod
    async def get_user(user_id: int) -> User:
        try:
            async with async_session() as session:
                stmt = select(User).where(User.user_id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                return user

        except Exception as e:
            logger.error(e)
            raise


class ImageORM:
    @staticmethod
    async def create_image(prompt: str, image_name: str, hash: str) -> GenerateImage:
        try:
            async with async_session() as session:
                image = GenerateImage(
                    prompt=prompt,
                    image_name=image_name,
                    hash=hash,
                )

                session.add(image)
                await session.commit()
                await session.refresh(image)

                return image

        except Exception as e:
            logger.error(e)

    @staticmethod
    async def get_image(id: int) -> GenerateImage:
        try:
            async with async_session() as session:
                stmt = select(GenerateImage).where(GenerateImage.id == id)
                result = await session.execute(stmt)
                image = result.scalar_one_or_none()

                if image is None:
                    return None

                return image

        except Exception as e:
            logger.error(e)
