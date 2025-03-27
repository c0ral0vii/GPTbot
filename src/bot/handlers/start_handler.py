from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.bot.keyboards.main_menu import main_menu_kb
from src.db.orm.bonus_links_orm import BonusLinksOrm
from src.db.orm.user_orm import UserORM
from src.utils.cached_user import _cached_user
from src.utils.logger import setup_logger
from src.scripts.queue.rabbit_queue import model
from src.utils.redis_cache.redis_cache import redis_manager

router = Router()
logger = setup_logger(__name__)


async def _check_bonus_link(message: types.Message, bonus_link: str):
    """Проверка бонусная ли ссылка в сообщении"""

    key = f"{message.from_user.id}:{bonus_link}"
    check_activate = await redis_manager.get(key)

    if not check_activate:
        bonus_link = await BonusLinksOrm.use_bonus_link(link=bonus_link)
        if bonus_link:
            await message.answer(
                f"❗Вы активировали бонусную ссылку на ⚡{float(bonus_link.energy_bonus)}"
            )
            await UserORM.add_energy(
                message.from_user.id, float(bonus_link.energy_bonus)
            )

            await redis_manager.set(key, value={"use": True})


async def _check_referral(message: types.Message):
    if len(message.text) < 7:
        await UserORM.create_user(
            message.from_user.id,
            username=message.from_user.username,
        )
        return

    logger.debug(f"All text {message.text}")
    referral_link = message.text.split(" ")[-1]

    if referral_link == "/start":
        await UserORM.create_user(
            message.from_user.id,
            username=message.from_user.username,
        )
        return

    if not referral_link.isdigit():
        await UserORM.create_user(
            message.from_user.id,
            username=message.from_user.username,
        )
        await _check_bonus_link(message, referral_link)
        return

    user = await UserORM.create_user(
        message.from_user.id,
        username=message.from_user.username,
        use_referral_link=int(referral_link),
    )
    logger.debug(user)

    if user.get("duplicate"):
        return

    owner = await UserORM.get_owner_referral(int(referral_link))

    if owner:
        await model.publish_message(
            queue_name="referral",
            user_id=owner.get("user_id"),
            text="❗ У вас новый рефералл, вы получили +20 ⚡ энергии.",
        )
        await UserORM.add_energy(message.from_user.id, 20)


@router.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    try:
        logger.debug(message.text)
        await state.clear()

        user_id = message.from_user.id
        key = f"{user_id}:user"

        await _check_referral(message)
        check_user = await UserORM.get_user(user_id)
        logger.debug(check_user)

        if check_user:
            link = message.text.split(" ")[-1]
            if link == "/start":
                await _check_bonus_link(message, link)

        if not check_user:
            await _cached_user(key, user_id)

            await message.answer(
                "Добро пожаловать в Woome AI 🧞‍\n\n️"
                "Вы получили 100 энергии – это 10 генераций уникального контента. \n"
                "Единственный ресурс, доступный без PRO. Как только он закончится – доступ к AI будет заблокирован.\n\n"
                "<u>Сейчас включён ОГРАНИЧЕННЫЙ РЕЖИМ:</u>\n"
                "❌ ChatGPT урезан – лимиты тормозят работу\n"
                "❌ Ассистенты отключены – доступны только в PRO\n"
                "❌ Когда энергия закончится – доступ будет отключен\n\n"
                "⚡ <u>PRO-доступ снимает все ограничения:</u>\n\n"
                "✅ Безлимитный ChatGPT и Claude – полная мощность\n"
                "✅ Ассистенты работают на тебя (докрутка статей, обход AI-детекторов, создание вирусного контента)\n"
                "✅ +2500 энергии – в 25 раз больше генераций, 25 раз больше возможностей\n"
                "✅ Приоритетная скорость обработки и мгновенные ответы (никакого ожидания)\n\n"
                "🛑 Разблокировать PRO -> /PRO",
                parse_mode="HTML",
                reply_markup=await main_menu_kb(),
            )
        else:
            user_info = await _cached_user(key, user_id)

            await message.answer(
                "Добро пожаловать в Woome AI 🧞\n\n"
                f"⚡ Ваш баланс: {user_info.get('energy', 0)}\n"
                f"{'✅' if user_info.get('check_premium') else '❌'} PRO-доступ: {'ЕСТЬ!' if user_info.get('check_premium') else 'НЕТ!'}\n\n"
                f"{'' if user_info.get('check_premium') else '🚨 Доступ к ассистентам заблокирован. Без PRO они не работают.\n\n'}"
                f"{'' if user_info.get('check_premium') else 'Разблокируй PRO и получи:\n'}"
                f"{'' if user_info.get('check_premium') else '✅ Безлимитный ChatGPT и Claude – работай без ограничений\n'}"
                f"{'' if user_info.get('check_premium') else '⚡ +2500 энергии – больше возможностей, больше действий\n'}"
                f"{'' if user_info.get('check_premium') else '🚀 Приоритетную скорость – запросы обрабатываются мгновенно\n'}"
                f"{'' if user_info.get('check_premium') else '🤖 Полный доступ ко всем ассистентам – генерация контента, тренды, аналитика, заработок\n\n'}"
                f"{'' if user_info.get('check_premium') else '💥 Каждый день без PRO – это потерянное время и деньги.\n\n'}"
                "🛠 <u>Попробуйте прямо сейчас</u>:\n"
                "• /text – Генерация текстов\n"
                "• /image – Создание изображений\n"
                "• /assistants – Работа с ассистентами\n\n"
                "⚙️ <u>Управление:</u>\n"
                "• /profile – Баланс генераций\n"
                "• /invite – Зарабатывай в Woome AI\n"
                f"• /PRO – Открыть PRO-доступ (+2500⚡)\n"
                "ℹ️ Хотите больше энергии? Откройте /menu",
                parse_mode="HTML",
                reply_markup=await main_menu_kb(),
            )

    except Exception as e:
        logger.error(e)
        await message.answer("Произошла ошибка, попробуйте еще раз")


@router.message(Command("invite"))
async def invite_handler(message: types.Message):
    try:
        await message.answer(
            "Приглашай друзей и зарабатывай!\n"
            "🔹 Как это работает? Пригласи друга и получи:\n\n"
            "1) мгновенно +20 ⚡энергии на баланс за каждого!\n"
            "2) 180 ₽ с каждой подписки по вашей ссылке 💰\n\n"
            "🔥 Чем больше друзей – тем больше бесплатных генераций и заработок!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Получить ссылку для заработка",
                            callback_data="get_refferall_link",
                        )
                    ]
                ]
            ),
        )
    except Exception as e:
        logger.error(e)
        await message.answer("Попробуйте прописать команду /start")


@router.callback_query(F.data == "get_refferall_link")
async def get_ref_link(callback: types.CallbackQuery):
    await callback.message.answer(
        f"Дарю тебе 20⚡ энергии в боте, где можно без VPN использовать ChatGPT и Claude! Запускай прямо сейчас и попробуй бесплатно: "
        f"https://t.me/{callback.message.from_user.username}?start={callback.from_user.id}",
    )


@router.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "🔹 Остались вопросы? Свяжитесь с поддержкой:\n" "👉 @WoomeSupport"
    )


@router.message(Command("menu"))
async def menu_command(message: types.Message):
    await message.answer(
        "📜 Меню Woome AI\n\n"
        "🔐 Без PRO ты работаешь в ограниченном режиме!\n\n"
        "💡 Зарабатывай с Woome AI\n"
        "🔗Зови друзей – получай +20⚡ энергии за каждого!\n"
        "📈 Получи проценты с их подписок\n"
        "👉 /invite — Пригласить друга\n\n"
        "⚙️ Доступные команды:\n"
        "• /text — Создавай тексты с ИИ\n"
        "• /assistants - Работа с ассистентами\n"
        "• /image — Генерируй изображения\n"
        "• /profile — Проверить баланс энергии\n"
        "• /pro — Открыть PRO и снять все ограничения\n\n"
        "💬 Нужна поддержка? Введите /help"
    )
