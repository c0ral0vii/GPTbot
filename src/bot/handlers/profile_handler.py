import html
from aiogram.filters import Command
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.bot.keyboards.profile import profile_settings_keyboard, change_settings
from src.db.enums_class import GPTConfig, CLAUDEConfig
from src.db.orm.config_orm import ConfigORM
from src.db.orm.user_orm import UserORM, PremiumUserORM
from src.utils.cached_user import _cached_user, change_settings_cache
from src.utils.logger import setup_logger

router = Router()
logger = setup_logger(__name__)


@router.message(F.text == "👤 Профиль")
@router.message(Command("profile"))
async def profile_handler(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        key = f"{user_id}:user"

        user_info = await _cached_user(key, user_id)

        if user_info is None:
            await UserORM.create_user(user_id)
            user_info = await _cached_user(key, user_id)

        if not user_info.get("check_premium"):
            await message.answer(
                f"👤Профиль: {html.escape(message.from_user.username)}\n\n"
                f"⚡ Энергия: {user_info.get("energy", 0)}\n"
                f"👥 Приглашённые друзья: {user_info.get("counts", 0)}\n"
                f"💰 Заработано с подписок: {user_info.get("referral_bonus", 0)}₽\n"
                f"❌ PRO-доступ: НЕТ!\n\n"
                f"🔒 Ассистенты заблокированы. Без PRO они не работают.\n\n"
                "<u>Что даёт PRO:</u>\n\n"
                "✅ Безлимитный ChatGPT и Claude – никаких лимитов, полный доступ\n"
                "⚡ +2500 энергии – больше возможностей, быстрее результаты\n"
                "🚀 Приоритетная скорость – никаких задержек, всё моментально\n"
                "🤖 Доступ ко ВСЕМ ассистентам – генерация контента, тренды, аналитика, заработок\n\n"
                "💥 Сейчас у тебя нет доступа. Каждый день без PRO – это потерянные деньги.\n\n",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="💳 РАЗБЛОКИРОВАТЬ PRO", callback_data="/PRO"
                            ),
                        ],
                        [
                            InlineKeyboardButton(
                                text="⚙️ Настройки", callback_data="settings"
                            ),
                        ],
                    ]
                ),
            )
        else:
            await message.answer(
                f"👤Профиль: {html.escape(message.from_user.username)}\n\n"
                f"⚡ Энергия: {user_info.get("energy", 0)}\n"
                f"👥 Приглашённые друзья: {user_info.get("counts", 0)}\n"
                f"💰 Заработано с подписок: {user_info.get("referral_bonus", 0)}₽\n"
                f"✅ PRO-доступ: ЕСТЬ!(Активен до {user_info.get("premium_to_date")})\n\n"
                f"⚙️ Управление подпиской:\n"
                "🔹 /subscription — Настройки подписки\n\n"
                "💰 Зарабатывайте вместе с Woome AI!\n\n"
                "Приглашайте друзей и получайте:\n"
                "✔️ +20⚡ энергии за каждого\n"
                "✔️ 180 ₽ с каждой подписки по вашей ссылке\n\n"
                "📢 Чем больше друзей – тем больше пассивного дохода!\n"
                "👉 /invite — Получить ссылку для заработка",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="⚙️Настройки", callback_data="settings"
                            ),
                        ]
                    ]
                ),
            )
    except Exception as e:
        logger.error(e)
        await message.answer("Произошла ошибка, попробуйте снова /start")


@router.callback_query(F.data == "settings")
async def settings_callback(callback: types.CallbackQuery):
    """Настройки"""

    await callback.message.answer(
        "`Модель: Выбранная версия`\n\nИзменение настроек:",
        parse_mode="Markdown",
        reply_markup=await profile_settings_keyboard(callback.from_user.id),
    )


@router.callback_query(F.data.startswith("change_"))
async def process_change_button(callback: types.CallbackQuery):
    choice = callback.data

    if choice == "change_chatgpt":
        # Логика для изменения настроек Chat GPT
        await callback.message.edit_reply_markup(
            reply_markup=await change_settings(callback.from_user.id, "gpt")
        )

    elif choice == "change_claude":
        # Логика для изменения настроек Claude
        await callback.message.edit_reply_markup(
            reply_markup=await change_settings(callback.from_user.id, "claude")
        )


@router.callback_query(F.data.startswith("setting_"))
async def change_model_settings(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    _, model_type, model_value = data.split("_", 2)  # Разделяем только по первому "_"

    try:
        if model_type == "gpt":
            change_setting = GPTConfig(model_value)
            await change_settings_cache(user_id, "gpt", model_value)

        elif model_type == "claude":
            change_setting = CLAUDEConfig(model_value)
            await change_settings_cache(user_id, "claude", model_value)

        else:
            await callback.answer("Неверный тип модели")
            return
    except ValueError:
        await callback.answer("Неверное значение модели")
        return

    user_config = await ConfigORM.change_config(user_id, change_setting=change_setting)

    if user_config:
        new_kb = await profile_settings_keyboard(user_id)
        await callback.message.edit_reply_markup(reply_markup=new_kb)
        await callback.answer(f"Модель изменена на {model_value}")
    else:
        await callback.answer("Ошибка при изменении настроек")
