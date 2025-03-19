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

async def send_premium_offer(target: types.Message | types.CallbackQuery, payment_link: str):
    """Отправляет сообщение с предложением о Premium подписке."""
    text = (
        "🌟 Оформи Premium и получи максимум возможностей!\n\n"
        "✅ Безлимитный ChatGPT и Claude – работай без ограничений\n"
        "⚡ +2500 энергии – больше запросов, больше возможностей\n"
        "🚀 Приоритетная скорость – никаких задержек, всё моментально\n"
        "🔒 Эксклюзивные функции и инструменты – только для PRO\n"
        "🤖 Полный доступ ко всем ассистентам – генерация контента, тренды, аналитика\n\n"
        "💰 Стоимость подписки: <s>3000</s> <b>1490 ₽</b> / месяц"
    )
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 ОПЛАТИТЬ И СНЯТЬ ОГРАНИЧЕНИЯ", url=payment_link)],
        ]
    )

    if hasattr(target, 'message'): 
        await target.message.answer(text, parse_mode="HTML", reply_markup=reply_markup)
    else:  
        await target.answer(text, parse_mode="HTML", reply_markup=reply_markup)
        
        
@router.message(Command("PRO", "pro"))
async def premium_text(message: types.Message):
    """Обработка команды /PRO."""
    await premium_handle(message)

@router.callback_query(F.data=="/PRO")
async def premium_callback(callback: types.CallbackQuery):
    """Обработка callback-запроса для Premium."""
    await premium_handle(callback)

async def premium_handle(target: types.Message | types.CallbackQuery):
    """Общая логика для обработки Premium."""
    check_premium = await PremiumUserORM.is_premium_active(target.from_user.id)

    if check_premium:
        text = "У вас уже есть активная подписка, чтобы узнать больше информации и управлять ей перейдите в /profile"
        if hasattr(target, 'message'):
            await target.message.answer(text)
        else:  
            await target.answer(text)
    else:
        payment_link = await generate_payment(target.from_user.id)
        await send_premium_offer(target, payment_link)


@router.message(Command("subscription"))
async def subscription_settings(message: types.Message):
    check_premium = await PremiumUserORM.is_premium_active(message.from_user.id)

    if check_premium:
        user = await _cached_user(f"{message.from_user.id}:user", message.from_user.id)

        if user["check_premium"] != check_premium:
            await update_premium(user_id=message.from_user.id, premium=check_premium)

        await message.answer(
            f"Дата окончания: {user['premium_to_date']}\n"
            f"Автопродление: {'✅' if user['settings']['auto_renewal'] else '❌'}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Изменить автопродление",
                            callback_data="sub_change_auto",
                        )
                    ],
                ]
            ),
        )
    else:
        await message.answer("Для начала оформи подписку -> /pro")


@router.callback_query(F.data == "sub_change_auto")
async def subscription_settings(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    user_config = await ConfigORM.change_config(
        auto_renewal=True,
        user_id=user_id,
    )

    check_premium = await PremiumUserORM.is_premium_active(user_id)
    user = await _cached_user(user_id=user_id)

    if user["check_premium"] != check_premium:
        await update_premium(user_id=user_id, premium=check_premium)

    if check_premium:
        await callback.message.edit_text(
            f"Дата окончания: {user['premium_to_date']}\n"
            f"Автопродление: {'✅' if user_config.auto_renewal else '❌'}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Изменить автопродление",
                            callback_data="sub_change_auto",
                        )
                    ],
                ]
            ),
        )
    else:
        await callback.message.answer(
            "❗У вас нет активной подписки для изменения пункта приобретите премиум\n\nДля покупки пропишите кнопку /premium"
        )
