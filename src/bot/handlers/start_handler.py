from aiogram import Router, types
from aiogram.filters import CommandStart

router = Router()


@router.message(CommandStart())
async def start_handler(message: types.Message):

    await message.answer(
        "Привет! 👋\n\n"
        "Тут ты можешь пообщаться с искусственным интеллектом. 🤖\n\n"
        "*Доступные команды:*\n"
        "• `/text` — Работа с текстом. \n"
        "• `/image` — Работа с изображениями. \n"
        "• `/code` — Работа с кодом. \n",
        parse_mode="Markdown",
    )
