from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.db.models import Dialog


async def select_text_gpt() -> InlineKeyboardMarkup:

    chat_gpt = InlineKeyboardButton(text="🤖 Chat GPT", callback_data="select_chatgpt")

    claude = InlineKeyboardButton(text="🤖 Claude", callback_data="select_claude")

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


async def get_models_dialogs(dialogs: list[Dialog] = None):

    if dialogs:
        user_dialogs = []
        for dialog in dialogs:
            user_dialogs.append(
                [
                    InlineKeyboardButton(
                        text=dialog.title, callback_data=f"dialog_{dialog.id}"
                    ),
                ]
            )
    else:
        user_dialogs = [
            [
                InlineKeyboardButton(
                    text="У вас пока нет диалогов!", callback_data="not_work"
                )
            ]
        ]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Новый диалог", callback_data="dialog_new")],
            *user_dialogs,
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )


async def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )


async def upgrade_message() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )


async def upgrade_photo(image_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for i in range(1, 5):
        kb.add(
            InlineKeyboardButton(
                text=f"Выбрать {i}", callback_data=f"upscale_{i}_{image_id}"
            )
        )

    for i in range(1, 5):
        kb.add(
            InlineKeyboardButton(
                text=f"Вариации {i}", callback_data=f"variation_{i}_{image_id}"
            )
        )

    kb.add(InlineKeyboardButton(text="🔄", callback_data=f"refresh_{image_id}"))
    # kb.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))

    kb.adjust(2, 2, 2, 2, 1)
    return kb.as_markup()
