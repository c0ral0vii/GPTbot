from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def main_menu_kb():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль")],
            [
                KeyboardButton(text="💡 Chat GPT/Claude"),
                KeyboardButton(text="🌄 MidJourney"),
            ],
            [
                KeyboardButton(text="🧑‍🔬 Ассистенты")
            ]
        ],
        resize_keyboard=True,
    )

    return kb
