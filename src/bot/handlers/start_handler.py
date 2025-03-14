from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.bot.keyboards.main_menu import main_menu_kb
from src.db.orm.user_orm import UserORM
from src.utils.cached_user import _cached_user
from src.utils.logger import setup_logger
from src.scripts.queue.rabbit_queue import model

router = Router()
logger = setup_logger(__name__)


async def _check_referral(message: types.Message):
    if len(message.text) < 7:
        await UserORM.create_user(message.from_user.id)
        return

    logger.debug(f"All text {message.text}")
    referral_link = message.text.split(" ")[-1]

    if referral_link == "/start":
        await UserORM.create_user(message.from_user.id)
        return

    if not referral_link.isdigit():
        return

    user = await UserORM.create_user(message.from_user.id, int(referral_link))
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
        user_id = message.from_user.id
        key = f"{user_id}:user"

        check_user = await _cached_user(key, user_id)
        logger.debug(check_user)

        if not check_user:
            await _check_referral(message)

            await message.answer(
                "Добро пожаловать в Woome AI 🧞‍\n\n️"
                "⚡ Вы бонусом получили 100 энергии (10 генераций) для создания уникальных текстов и изображений с помощью ИИ!\n"
                "🛠 Попробуйте прямо сейчас:\n\n"
                "• /text — Генерация текстов\n"
                "• /image — Создание изображений\n\n"
                "⚙️ Управление:\n\n"
                "• /profile — Баланс генераций\n"
                "• /invite — Зарабатывай в Woome AI\n"
                "• /premium — 🌟 Premium подписка (+2500⚡)\n\n"
                "ℹ️ Хотите больше энергии? Откройте /menu",
                parse_mode="Markdown",
                reply_markup=await main_menu_kb(),
            )
        else:
            await message.answer(
                "Добро пожаловать в Woome AI 🧞‍\n\n️"
                f"Ваш баланс: {check_user.get('energy')} ⚡\n"
                f"Premium подписка: {"✅" if check_user.get('check_premium') else "❌"} \n\n"
                "🛠 Попробуйте прямо сейчас:\n\n"
                "• /text — Генерация текстов\n"
                "• /image — Создание изображений\n\n"
                "⚙️ Управление:\n\n"
                "• /profile — Баланс генераций\n"
                "• /invite — Зарабатывай в Woome AI\n"
                "• /premium — 🌟 Premium подписка (+2500⚡)\n\n"
                "ℹ️ Хотите больше энергии? Откройте /menu",
                parse_mode="Markdown",
                reply_markup=await main_menu_kb(),
            )

        await state.clear()
    except Exception as e:
        logger.error(e)
        await message.answer("Произошла ошибка, попробуйте еще раз")


@router.message(Command("invite"))
async def invite_handler(message: types.Message):
    try:
        await message.answer("Приглашай друзей и зарабатывай!\n"
                             "🔹 Как это работает? Пригласи друга и получи:\n\n"
                             "1) мгновенно +20 ⚡энергии на баланс за каждого!\n"
                             "2) 180 ₽ с каждой подписки по вашей ссылке 💰\n\n"
                             "🔥 Чем больше друзей – тем больше бесплатных генераций и заработок!",
                             parse_mode="Markdown",
                             reply_markup=InlineKeyboardMarkup(
                                 inline_keyboard=[
                                     [InlineKeyboardButton(text="Получить ссылку для заработка", callback_data="get_refferall_link")]
                                 ]
                             ),)
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
    await message.answer("🔹 Остались вопросы? Свяжитесь с поддержкой:\n"
                         "👉 @WoomeSupport")


@router.message(Command("menu"))
async def menu_command(message: types.Message):
    await message.answer("📜 Меню Woome AI\n\n"
                         "🌟 С Premium подпиской ChatGPT и Claude становятся безлимитны!\n"
                         "⚡+2500 энергии всего за 1490 ₽ 👉 /premium\n\n"
                         "Зови друзей – получай +20⚡ энергии мгновенно и зарабатывай на их подписках!\n"
                         " 👉 /invite — Пригласить друга\n\n"
                         "⚙️ Доступные команды:\n\n"
                         "• /text — Создавай тексты с ИИ\n"
                         "• /image — Генерируй изображения\n"
                         "• /profile — Проверить баланс энергии\n"
                         "• /premium — 🌟 Оформить подписку и снять ограничения\n\n"
                         "💬 Нужна поддержка? Введите /help")