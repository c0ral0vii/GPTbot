from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def select_text_gpt() -> InlineKeyboardMarkup:

    chat_gpt = InlineKeyboardButton(
        text="Chat GPT o1", callback_data="select_chat_gpt_o1"
    )
    claude = InlineKeyboardButton(
        text="Claude (Anthropic)", callback_data="select_claude"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [chat_gpt],
            [claude],
        ],
    )

    return kb


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
        ]
    )


def upgrade_message() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Доработать", callback_data="upgrade_message"
                ),
                InlineKeyboardButton(text="Сохранить", callback_data="save_message"),
            ],
            [InlineKeyboardButton(text="Переслать", callback_data="retwit_message")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
        ]
    )
