from aiogram.filters import Command
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from src.db.orm.user_orm import UserORM
from src.utils.logger import setup_logger

router = Router()
logger = setup_logger(__name__)


@router.message(F.text == "👤 Профиль")
@router.message(Command("profile"))
async def profile_handler(message: types.Message, state: FSMContext):
    try:
        profile_info = await UserORM.get_user(message.from_user.id)
        referrals = await UserORM.get_count_referrals(message.from_user.id)

        await message.answer(
            f"*👤 Профиль {message.from_user.username}:*\n\n"
            f"⚡ Энергия: {profile_info.energy}\n"
            f"👥 Рефералы: {referrals} человек\n\n"
            "Приглашайте новых участников для получения энергии /invite!",

            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(e)
        await message.answer("Произошла ошибка, попробуйте снова /start")
