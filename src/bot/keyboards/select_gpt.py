from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def select_text_gpt() -> InlineKeyboardMarkup:

    chat_gpt = InlineKeyboardButton(text="🤖 Chat GPT", callback_data="select_chat_gpt")

    claude = InlineKeyboardButton(
        text="🤖 Claude Sonnet", callback_data="select_claude"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [chat_gpt],
            [claude],
        ],
    )

    return kb


def select_image_model() -> InlineKeyboardMarkup:

    mj = InlineKeyboardButton(text="🤖 Midjourney", callback_data="select_midjourney")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [mj],
        ]
    )

    return kb


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )


def upgrade_message() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Доработать", callback_data="upgrade_message"
                ),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )


async def upgrade_photo(image_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for i in range(1, 5):
        kb.add(
            InlineKeyboardButton(text=f"U{i}", callback_data=f"upscale_{i}_{image_id}")
        )

    for i in range(1, 5):
        kb.add(
            InlineKeyboardButton(
                text=f"V{i}", callback_data=f"variation_{i}_{image_id}"
            )
        )

    kb.add(InlineKeyboardButton(text="🔄", callback_data=f"refresh_{image_id}"))
    kb.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))

    kb.adjust(2, 2, 2, 2, 1, 1)
    return kb.as_markup()
