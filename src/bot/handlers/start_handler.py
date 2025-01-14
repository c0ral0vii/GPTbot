from aiogram import Router, types
from aiogram.filters import CommandStart

from src.bot.keyboards.main_menu import main_menu_kb

router = Router()


@router.message(CommandStart())
async def start_handler(message: types.Message):

    await message.answer(
        "Выберите нейросеть:\n\n"
        "*🤖 Чат-ассистенты::*\n\n"
        "• /text — Работа с текстом. \n"
        "• /image — Работа с изображениями. \n"
        "• /code — Работа с кодом. \n"
        "\n*⚙️ Управление:* \n\n"
        "• /profile — Баланс генераций \n"
        "• /invite — Пригласить друга (+20💎 генераций) \n"
        "• /bonus — Бесплатный нейро-курс (до +70💎 генераций) \n"
        "• /premium — 🌟 Premium подписка (1000💎 генераций) \n\n"
        "/start — Сменить нейросеть",

    parse_mode="Markdown",
    reply_markup=await main_menu_kb(),
    )
