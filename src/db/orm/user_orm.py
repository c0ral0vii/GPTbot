from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any

from sqlalchemy.orm import selectinload, joinedload

from src.db.models import User, GenerateImage, PremiumUser, BannedUser
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
    async def get_user(user_id: int) -> User | None:
        async with async_session() as session:
            try:
                stmt = select(User).where(User.user_id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                if not user:
                    return None

                return user

            except Exception as e:
                logger.error(e)
                raise


class ImageORM:
    @staticmethod
    async def create_image(
        prompt: str, image_name: str, hash: str, first_hash: str | None
    ) -> GenerateImage:
        try:
            async with async_session() as session:
                image = GenerateImage(
                    prompt=prompt,
                    image_name=image_name,
                    hash=hash,
                    first_hash=first_hash if first_hash else None,
                )

                session.add(image)
                await session.commit()
                await session.refresh(image)

                return image

        except Exception as e:
            logger.error(e)

    @staticmethod
    async def get_image(id: int) -> GenerateImage | None:
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

    @staticmethod
    async def change_image_hash(image_id: int | str, hash: str) -> bool:
        if isinstance(image_id, str) and image_id.isdigit():
            image_id = int(image_id)

        async with async_session() as session:
            try:
                stmt = select(GenerateImage).where(GenerateImage.id == image_id)
                result = await session.execute(stmt)
                image = result.scalar_one_or_none()
                if not image:
                    return False

                image.hash = hash

                session.add(image)
                await session.commit()
                await session.refresh(image)

            except Exception as e:
                logger.error(e)
                return False


class AnalyticsORM:
    @staticmethod
    async def get_user_for_analytics() -> Optional[dict[str, int]]:
        today = datetime.today().date()
        async with async_session() as session:
            stmt = select(func.count(User.id))
            result = await session.execute(stmt)
            total_users_count = result.scalar()

            stmt = select(func.count(User.id)).where(func.date(User.updated) == today)
            result = await session.execute(stmt)
            active_users_today_count = result.scalar()

            stmt = select(func.count(User.id)).join(PremiumUser).where(PremiumUser.premium_active == True)
            result = await session.execute(stmt)
            premium_users_count = result.scalar()

            data = {
                "total_users_count": total_users_count,
                "active_users_today_count": active_users_today_count,
                "premium_users_count": premium_users_count,
                "revenue": premium_users_count,
            }
            return data


    @staticmethod
    async def get_activity_users():
        hours = list(range(24))
        values = []
        today = datetime.today().date()
        async with async_session() as session:
            for hour in hours:
                start_time = datetime.combine(today, datetime.min.time()) + timedelta(hours=hour)
                end_time = start_time + timedelta(hours=1)

                # Получаем количество пользователей, которые были активны в этот час
                stmt = select(func.count(User.id)).where(
                    User.updated >= start_time, User.updated < end_time
                )
                result = await session.execute(stmt)
                active_users_count = result.scalar()

                values.append(active_users_count)

            return {"labels": hours, "values": values}


    @staticmethod
    async def get_all_users_analytics():
        async with async_session() as session:
            result = []

            stmt_users = select(User).options(selectinload(User.premium_status))
            result_users = await session.execute(stmt_users)
            users = result_users.scalars().all()

            for user in users:
                created_date = user.created.strftime('%H:%M:%S %Y-%m-%d') if user.created else None
                last_used_date = user.updated.strftime('%H:%M:%S %Y-%m-%d') if user.updated else None
                user_data = {
                    "table": "users",
                    "id": user.id,
                    "user_id": user.user_id,
                    "energy": float(user.energy) if user.energy else None,
                    "referral_link": user.referral_link,
                    "use_referral_link": user.use_referral_link,
                    "status": user.premium_status.premium_active if user.premium_status else False,
                    "premium_dates": {
                        "premium_active": user.premium_status.premium_active if user.premium_status else None,
                        "premium_to_date": user.premium_status.premium_to_date.isoformat() if user.premium_status and user.premium_status.premium_to_date else None,
                    } if user.premium_status else None,
                    "created": created_date,
                    "updated": last_used_date,
                }
                result.append(user_data)

            return result

    @staticmethod
    async def get_all_user_info(user_id: int):
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id).options(selectinload(User.premium_status))
            result = await session.execute(stmt)
            user = result.scalars().first()

            stmt = select(BannedUser).where(BannedUser.user_id == user.user_id)
            result = await session.execute(stmt)
            banned_user = result.scalars().first()

            if not banned_user:
                banned = False
            else:
                banned = True
            created_date = user.created.strftime('%H:%M:%S %Y-%m-%d') if user.created else None
            last_used_date = user.updated.strftime('%H:%M:%S %Y-%m-%d') if user.updated else None

            return {
                "user_id": user.user_id,
                "energy": float(user.energy),
                "referral_link": user.referral_link,
                "use_referral_link": user.use_referral_link,
                "status": True if user.premium_status else False,
                "banned_user": banned,
                "created": created_date,
                "last_used": last_used_date,
            }

    @staticmethod
    async def banned_user(user_id: int):
        async with async_session() as session:
            try:
                banned_user = BannedUser(
                    user_id=user_id,
                )

                session.add(banned_user)
                await session.commit()
            except IntegrityError:
                await session.rollback()
            except Exception as e:
                await session.rollback()

    @staticmethod
    async def change_user(user_id, data):
        async with async_session() as session:
            ...