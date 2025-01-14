from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def main_menu_kb():
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.add(KeyboardButton(text="👤 Профиль"))
    kb.row(KeyboardButton(text="💡 Chat GPT/Claude"), KeyboardButton(text="🌄 MidJourney"))

    return kb