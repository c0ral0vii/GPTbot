from typing import Literal
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


async def paginate_models_dialogs(
    callback: Literal["dialog_", "config_dialog_"],
    page: int = 1,
    max_pages: int = 1,
    data: list[Dialog] = None,
    per_page: int = 5,
    change_button: bool = True,
):
    """Пагинация для диалогов"""

    user_dialogs = []
    for dialog in data:
        callback_data = f"{callback}{dialog.id}"
        user_dialogs.append(
            [
                InlineKeyboardButton(
                    text=dialog.title, callback_data=callback_data
                ),
            ]
        )

    pagination_buttons = []
    if max_pages > 1:
        if page > 1:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ Предыдущая", callback_data=f"page_previous"
                )
            )

        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"🔢 {page}/{max_pages}", callback_data="current_page"
            )
        )

        if page < max_pages:
            pagination_buttons.append(
                InlineKeyboardButton(text="Следующая ➡️", callback_data=f"page_next")
            )

    if change_button:
        keyboard = [
            [InlineKeyboardButton(text="➕ Новый диалог", callback_data="dialog_new")],
            *user_dialogs,
        ]
    else:
        keyboard = [
            *user_dialogs,
        ]

    if pagination_buttons:
        keyboard.append(pagination_buttons)

    if change_button:
        keyboard.append([InlineKeyboardButton(text="🖋 Изменить диалоги", callback_data="configs_dialog")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


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
            [InlineKeyboardButton(text="🖋 Изменить диалоги", callback_data="configs_dialog")],
        ]
    )

async def change_dialog_kb(dialog_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🖋 Изменить диалог", callback_data=f"config_dialog_{dialog_id}")],
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
