from typing import Any, Literal

from src.utils.redis_cache.redis_cache import redis_manager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


async def _cached_user(
    key: str = None, user_id: int = None, refresh: bool = False
) -> dict[str, Any] | None:
    """Кешировавние пользовавтеля"""
    key = f"{user_id}:user"

    find_info = await redis_manager.get(key=key)
    logger.debug(find_info)
    from src.db.orm.user_orm import UserORM

    if find_info is None or refresh:

        user = await UserORM.get_user(user_id=user_id, get_premium_status=True)

        if not user:
            return None

        counts = await UserORM.get_count_referrals(user_id)

        data = {
            "user_id": user_id,
            "energy": float(user["user"].energy),
            "personal_percent": user["user"].personal_percent,
            "referral_bonus": float(user["user"].referral_bonus),
            "check_premium": user["premium_status"],
            "settings": {
                "gpt_select": user["user"].user_config_model.gpt_select.value,
                "claude_select": user["user"].user_config_model.claude_select.value,
                "auto_renewal": user["user"].user_config_model.auto_renewal,
            },
        }
        user["counts"] = counts

        logger.debug(data)

        await redis_manager.set(key=key, value=data, ttl=604800)
        return data
    else:
        counts = await UserORM.get_count_referrals(user_id)
        user = await redis_manager.get(key=key)

        user["counts"] = counts

        await redis_manager.set(key=key, value=user, ttl=604800)
        return user


async def check_user_create(user_id: int) -> dict | None:
    """Проверка состояния создания пользователя"""

    key = f"{user_id}:referral"

    find_info = await redis_manager.get(key=key)
    if not find_info:
        return None
    return find_info


async def create_referral_user(user_id: int) -> None:
    """Создание пользователя в реферальной системе redis"""

    key = f"{user_id}:referral"
    await redis_manager.set(key=key, value={"user_id": user_id}, ttl=604800)


async def update_user_count(user_id: int) -> None:
    """Создайние или обновление количества рефералов пользователя"""

    key = f"{user_id}:user"
    from src.db.orm.user_orm import UserORM

    counts = await UserORM.get_count_referrals(user_id)
    user = await redis_manager.get(key=key)

    user["counts"] = counts

    await redis_manager.set(key=key, value=user, ttl=604800)


async def update_energy_cache(user_id: int, new_energy: float) -> None:
    key = f"{user_id}:user"
    user = await redis_manager.get(key=key)

    if not user:
        user = await _cached_user(key=key, user_id=user_id)

    user["energy"] = float(new_energy)

    await redis_manager.set(key=key, value=user, ttl=604800)


async def update_premium(user_id: int, premium: bool) -> None:
    key = f"{user_id}:user"
    user = await redis_manager.get(key=key)

    if not user:
        user = await _cached_user(key=key, user_id=user_id)

    user["check_premium"] = premium
    if premium is True:
        await _cached_user(key=key, user_id=user_id, refresh=True)
        return

    await redis_manager.set(key=key, value=user, ttl=604800)


async def change_settings_cache(
    user_id: int, gpt_type: Literal["claude", "gpt"], new_value: str
) -> None:
    key = f"{user_id}:user"
    user = await redis_manager.get(key=key)

    if not user:
        user = await _cached_user(key=key, user_id=user_id)

    if gpt_type == "claude":
        user["settings"]["claude_select"] = new_value
    else:
        user["settings"]["gpt_select"] = new_value

    await redis_manager.set(key=key, value=user, ttl=604800)


async def change_premium_status(user_id: int, premium: bool, premium_to_date) -> None:
    key = f"{user_id}:user"
    user = await redis_manager.get(key=key)
    if not user:
        return

    user["check_premium"] = premium

    if premium_to_date is not None:
        formatted_date = premium_to_date.strftime("%d.%m.%Y")
        user["premium_to_date"] = formatted_date
    else:
        user["premium_to_date"] = None

    await redis_manager.set(key=key, value=user, ttl=604800)
