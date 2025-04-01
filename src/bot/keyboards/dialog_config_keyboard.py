from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def dialog_config_keyboard(dialog_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Переименовать",
                    callback_data=f"chg_{dialog_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Получить полный диалог(СКОРО)",
                    callback_data=f"get_full_dialog_{dialog_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Удалить диалог", callback_data=f"delete_dialog_{dialog_id}"
                )
            ],
        ]
    )
    return keyboard
