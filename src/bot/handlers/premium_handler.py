from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.db.orm.config_orm import ConfigORM
from src.db.orm.user_orm import PremiumUserORM
from src.utils.cached_user import _cached_user, update_premium
from src.utils.generate_payment import generate_payment
from src.utils.logger import setup_logger

router = Router()
logger = setup_logger(__name__)
PRIVACY_POLICY = "https://gradov.online/ofertaneurokesh"


@router.message(Command("premium"))
async def premium_handle(message: types.Message):
    check_premium = await PremiumUserORM.is_premium_active(message.from_user.id)

    if check_premium:
        await message.answer("У вас уже есть активная подписка, чтобы узнать больше информации и управлять ей перейдите в /profile")
    else:
        payment_link = await generate_payment(message.from_user.id)

        await message.answer(
            "🌟 Оформи Premium и получи максимум возможностей!\n\n"
            f"🔹 Что даёт подписка?\n"
            "✅ ChatGPT и Claude становятся безлимитными\n"
            "⚡ +2 500 энергии для других ИИ\n"
            "🚀 Приоритетная скорость обработки запросов\n"
            "🔒 Доступ к эксклюзивным функциям в будущем\n\n"
            "Стоимость подписки: 1490 рублей за 1 месяц использования",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Оплатить", url=payment_link)],
                ]
            ),
        )


@router.message(Command("subscription"))
async def subscription_settings(message: types.Message):
    check_premium = await PremiumUserORM.is_premium_active(message.from_user.id)

    if check_premium:
        user = await _cached_user(f"{message.from_user.id}:user", message.from_user.id)

        if user["check_premium"] != check_premium:
            await update_premium(user_id=message.from_user.id, premium=check_premium)

        await message.answer(f"Дата окончания: {user['premium_to_date']}\n"
                             f"Автопродление: {'✅' if user['settings']['auto_renewal'] else '❌'}", reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Изменить автопродление", callback_data="sub_change_auto")],
            ]
        ))
    else:
        await message.answer("Для начала оформи подписку -> /premium")

@router.callback_query(F.data == "sub_change_auto")
async def subscription_settings(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    await ConfigORM.change_config(
        auto_renewal=True,
        user_id=user_id,
    )

    check_premium = await PremiumUserORM.is_premium_active(user_id)
    user = await _cached_user(user_id=user_id)

    if user["check_premium"] != check_premium:
        await update_premium(user_id=user_id, premium=check_premium)

    if check_premium:

        await callback.message.edit_text(f"Дата окончания: {user['premium_to_date']}\n"
                             f"Автопродление: {'✅' if user['settings']['auto_renewal'] else '❌'}",)
    else:
        await callback.message.answer("❗У вас нет активной подписки для изменения пункта приобретите премиум\n\nДля покупки пропишите кнопку /premium")
