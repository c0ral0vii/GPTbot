from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import User, GenerateImage, PremiumUser, BannedUser, BonusLink
from src.db.orm.config_orm import ConfigORM
from src.utils.cached_user import (
    create_referral_user,
    check_user_create,
    _cached_user,
    update_energy_cache,
    change_premium_status,
)
from src.utils.logger import setup_logger

from src.db.database import async_session
from sqlalchemy import select, func, or_, cast, String
from sqlalchemy.exc import IntegrityError


logger = setup_logger(__name__)


class PremiumUserORM:
    @staticmethod
    async def is_premium_active(user_id: int, session: AsyncSession = None) -> bool:
        """
        Проверяет, активна ли премиум-подписка пользователя.
        Возвращает:
            - True, если подписка активна.
            - False, если подписка истекла или отсутствует.
        """
        if not session:
            session = async_session()

        stmt = (
            select(User)
            .where(User.user_id == user_id)
            .options(selectinload(User.premium_status))
        )
        result = await session.execute(stmt)
        premium_user = result.scalar_one_or_none()

        if not premium_user or not premium_user.premium_status:
            if not session:
                await session.close()

            return False

        if premium_user.premium_status.premium_to_date < datetime.now().date():
            premium_user.premium_status.premium_active = False
            await change_premium_status(
                user_id=user_id, premium=False, premium_to_date=None
            )

            await session.commit()
            if not session:
                await session.close()

            return False

        if not session:
            await session.close()
        await change_premium_status(
            user_id=user_id,
            premium=True,
            premium_to_date=premium_user.premium_status.premium_to_date,
        )
        return True


class UserORM:
    @staticmethod
    async def create_premium_user(
        user_id: int, payment_method_id: str
    ) -> Optional[PremiumUser]:
        today = datetime.now().date()
        end_date = today + timedelta(days=30)

        async with async_session() as session:
            stmt = (
                select(User)
                .where(User.user_id == user_id)
                .options(selectinload(User.premium_status))
            )

            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            premium_user = PremiumUser(
                premium_active=True,
                premium_from_date=today,
                premium_to_date=end_date,
                auth_renewal_id=payment_method_id,
                user_id=user.id,
            )

            if user:
                user.premium_status = premium_user
            else:
                session.add(premium_user)

            if user.use_referral_link:
                stmt = select(User).where(User.user_id == user.use_referral_link)
                result = await session.execute(stmt)
                ref_user = result.scalar_one_or_none()

                if ref_user:
                    ref_user.referral_bonus = ref_user.referral_bonus + Decimal(180)
                    session.add(ref_user)

            await session.commit()
            await _cached_user(user_id=user_id, refresh=True)
            await _cached_user(user_id=user.use_referral_link, refresh=True)

            await change_premium_status(
                user_id=user_id, premium=True, premium_to_date=end_date
            )

            return premium_user

    @staticmethod
    async def create_user(
        user_id: int, use_referral_link: int = None
    ) -> dict[str, Any]:
        try:
            async with async_session() as session:
                stmt = select(User).where(User.user_id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    return {"duplicate": True}

                existing_referral = await check_user_create(user_id)
                if not existing_referral and use_referral_link:
                    await create_referral_user(user_id=use_referral_link)

                    check_status = await UserORM.get_owner_referral(use_referral_link)
                    if not check_status:
                        use_referral_link = None

                new_user = User(
                    user_id=user_id,
                    use_referral_link=use_referral_link,
                )

                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)

                await ConfigORM.create_config(new_user)

                return {"duplicate": False}
        except IntegrityError:
            return {"duplicate": True}
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {e}")
            return {"duplicate": True}

    @staticmethod
    async def get_owner_referral(referral_code: int) -> Dict[str, Any] | None:
        try:
            user = await check_user_create(referral_code)
            if user:
                return user

            async with async_session() as session:
                stmt = select(User).where(User.user_id == referral_code)
                result = await session.execute(stmt)
                owner = result.scalar_one_or_none()

                if owner:
                    return {"user_id": owner.user_id}

                return None
        except Exception as e:
            logger.error(f"Error fetching owner referral {referral_code}: {e}")
            return None

    @staticmethod
    async def remove_energy(user_id: int, count: int | str) -> Dict[str, Any]:
        try:
            async with async_session() as session:
                stmt = select(User).where(User.user_id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if user.energy >= count:
                    user.energy = user.energy - Decimal(count)
                    await update_energy_cache(
                        user_id=user.user_id, new_energy=float(user.energy)
                    )
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
                await update_energy_cache(
                    user_id=user.user_id, new_energy=float(user.energy)
                )

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

                return user.user_id

        except Exception as e:
            logger.error(e)
            raise

    @staticmethod
    async def get_count_referrals(user_id: int) -> int:
        try:
            async with async_session() as session:
                # stmt = select(User).where(User.user_id == user_id)
                # result = await session.execute(stmt)
                # user = result.scalar_one_or_none()

                stmt = select(func.count()).where(User.use_referral_link == user_id)

                result = await session.execute(stmt)
                referrals_count = result.scalar()

                return referrals_count
        except Exception as e:
            logger.error(e)
            raise

    @staticmethod
    async def get_user(
        user_id: int, get_premium_status: bool = False
    ) -> User | None | dict[str, Any]:
        async with async_session() as session:
            try:
                stmt = (
                    select(User)
                    .where(User.user_id == user_id)
                    .options(
                        selectinload(User.premium_status),
                        selectinload(User.user_config_model),
                    )
                )
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if not user:
                    return None

                if get_premium_status:
                    premium_status = await PremiumUserORM.is_premium_active(
                        user_id, session
                    )
                    return {"user": user, "premium_status": premium_status}

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

            stmt = (
                select(func.count(User.id))
                .join(PremiumUser)
                .where(PremiumUser.premium_active == True)
            )
            result = await session.execute(stmt)
            premium_users_count = result.scalar()
            non_premium_users_count = total_users_count - premium_users_count
            data = {
                "non_premium_users_count": non_premium_users_count,
                "total_users_count": total_users_count,
                "active_users_today_count": active_users_today_count,
                "premium_users_count": premium_users_count,
                "revenue": 990 * premium_users_count,
            }
            return data

    @staticmethod
    async def get_activity_users_per_24h():
        hours = list(range(24))
        values = []
        today = datetime.today().date()
        async with async_session() as session:
            for hour in hours:
                start_time = datetime.combine(today, datetime.min.time()) + timedelta(
                    hours=hour
                )
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
    async def get_activity_users():
        days = [
            (datetime.today().date() - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(6, -1, -1)
        ]
        values = []

        async with async_session() as session:
            for day in days:
                start_time = datetime.strptime(day, "%Y-%m-%d")
                end_time = start_time + timedelta(days=1)

                # Получаем количество пользователей, активных в этот день
                stmt = select(func.count(User.id)).where(
                    User.updated >= start_time, User.updated < end_time
                )
                result = await session.execute(stmt)
                active_users_count = result.scalar()

                values.append(active_users_count or 0)

        return {"labels": days, "values": values}

    @staticmethod
    async def get_all_users_analytics(
        search: str = "",
    ):
        async with async_session() as session:
            result = []

            stmt_users = select(User).options(selectinload(User.premium_status), selectinload(User.user_config_model))

            if search != "":
                stmt_users = stmt_users.where(
                    or_(
                        cast(User.user_id, String).ilike(f"%{search}%"),
                    )
                )

            result_users = await session.execute(stmt_users)
            users = result_users.scalars().all()

            for user in users:
                created_date = (
                    user.created.strftime("%H:%M:%S %Y-%m-%d") if user.created else None
                )
                last_used_date = (
                    user.updated.strftime("%H:%M:%S %Y-%m-%d") if user.updated else None
                )
                user_data = {
                    "table": "users",
                    "id": user.id,
                    "user_id": user.user_id,
                    "energy": float(user.energy) if user.energy else None,
                    "use_referral_link": user.use_referral_link,

                    "personal_percent": user.personal_percent,
                    "referral_bonus": user.referral_bonus,
                    "auto_renewal": user.user_config_model.auto_renewal,

                    "status": (
                        user.premium_status.premium_active
                        if user.premium_status
                        else False
                    ),

                    "premium_dates": (
                        {
                            "premium_active": (
                                user.premium_status.premium_active
                                if user.premium_status
                                else None
                            ),
                            "premium_to_date": (
                                user.premium_status.premium_to_date.isoformat()
                                if user.premium_status
                                and user.premium_status.premium_to_date
                                else None
                            ),
                        }
                        if user.premium_status
                        else None
                    ),
                    "created": created_date,
                    "updated": last_used_date,
                }
                result.append(user_data)

            return result

    @staticmethod
    async def get_all_user_info(user_id: int):
        async with async_session() as session:
            stmt = (
                select(User)
                .where(User.id == user_id)
                .options(selectinload(User.premium_status), selectinload(User.user_config_model))
            )
            result = await session.execute(stmt)
            user = result.scalars().first()

            if not user:
                return {"error": "User not found"}

            stmt = select(BannedUser).where(BannedUser.user_id == user.id)
            result = await session.execute(stmt)
            banned_user = result.scalars().first()

            created_date = (
                user.created.strftime("%H:%M:%S %Y-%m-%d") if user.created else None
            )
            last_used_date = (
                user.updated.strftime("%H:%M:%S %Y-%m-%d") if user.updated else None
            )

            premium_status = user.premium_status
            premium_active = premium_status.premium_active if premium_status else False
            premium_from = (
                premium_status.premium_from_date.strftime("%Y-%m-%d")
                if premium_status and premium_status.premium_from_date
                else None
            )
            premium_to = (
                premium_status.premium_to_date.strftime("%Y-%m-%d")
                if premium_status and premium_status.premium_to_date
                else None
            )

            return {
                "user_id": user.user_id,
                "energy": float(user.energy),
                "use_referral_link": user.use_referral_link,

                "personal_percent": user.personal_percent,
                "referral_bonus": user.referral_bonus,
                "auto_renewal": user.user_config_model.auto_renewal,

                "premium_active": premium_active,
                "premium_dates": (
                    {"from": premium_from, "to": premium_to} if premium_active else None
                ),
                "banned_user": True if banned_user else False,
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
    async def change_user(user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        async with async_session() as session:
            stmt = (
                select(User)
                .where(User.id == user_id)
                .options(selectinload(User.premium_status))
            )
            result = await session.execute(stmt)
            user = result.scalars().first()

            if not user:
                return {"error": "User not found"}

            # Обновляем основные данные пользователя
            await AnalyticsORM._banned_user_or_unbanned(
                user_id=user.id, session=session, ban=data.get("banned_user", False)
            )
            user.energy = Decimal(data["energy"])
            if data.get("use_referral_link") == "":
                user.use_referral_link = None
            else:
                user.use_referral_link = data.get("use_referral_link", None)

            # Обрабатываем премиум-статус
            if data.get("premium_active"):
                premium_dates = data.get("premium_dates", {})
                premium_from = premium_dates.get("from")
                premium_to = premium_dates.get("to")

                if premium_from and premium_to:
                    premium_from = date.fromisoformat(premium_from)
                    premium_to = date.fromisoformat(premium_to)

                    if user.premium_status:
                        # Обновляем существующую премиум-запись
                        user.premium_status.premium_active = True
                        user.premium_status.premium_from_date = premium_from
                        user.premium_status.premium_to_date = premium_to
                    else:
                        # Создаём новую премиум-запись
                        new_premium = PremiumUser(
                            user_id=user.id,
                            premium_active=True,
                            premium_from_date=premium_from,
                            premium_to_date=premium_to,
                        )
                        session.add(new_premium)
            else:
                # Если премиум выключен, удаляем статус, если он был
                if user.premium_status:
                    await session.delete(user.premium_status)

            session.add(user)
            await session.commit()
            return {"success": True, "user_id": user.id}

    @staticmethod
    async def _banned_user_or_unbanned(
        user_id: int, session: AsyncSession, ban: bool
    ) -> bool:
        stmt = select(BannedUser).where(BannedUser.user_id == user_id)
        result = await session.execute(stmt)
        banned_user = result.scalars().one_or_none()

        if ban:
            if not banned_user:
                new_banned_user = BannedUser(user_id=user_id)
                session.add(new_banned_user)
        else:
            if banned_user:
                await session.delete(banned_user)

        await session.commit()
        return True

    @staticmethod
    async def add_or_change_promo(data: Dict[str, Any]):
        async with async_session() as session:
            stmt = select(BonusLink).where(data.get("link"))
            result = await session.execute(stmt)
            bonus_link = result.scalars().one_or_none()
            if data.get("active_count", 0) <= 0:
                data["active"] = False

            if bonus_link:
                bonus_link.active = data.get("active", False)
                bonus_link.active_count = data.get("active_count", 0)
                bonus_link.energy_bonus = Decimal(data.get("energy_bonus", 0))
                await session.commit()
                return {"success": True}

            new_bonus_link = BonusLink(
                energy_bonus=Decimal(data.get("energy_bonus", 0)),
                link=data.get("link"),
                active=data.get("active", False),
                active_count=data.get("active_count", 0),
            )
            session.add(new_bonus_link)
            await session.commit()
            return {"success": True}


class BannedUserORM:
    @staticmethod
    async def check_banned_user(user_id: int) -> bool:
        async with async_session() as session:
            stmt = select(BannedUser).where(BannedUser.user_id == user_id)
            result = await session.execute(stmt)
            banned_user = result.scalars().one_or_none()

            if banned_user:
                return True
            return False
