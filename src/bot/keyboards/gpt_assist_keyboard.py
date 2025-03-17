from typing import List, Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.db.models import GPTAssistant


async def gpt_assist_keyboard(assits: Optional[List[GPTAssistant]],
                              premium: Optional[bool]) -> InlineKeyboardMarkup:

    input_kb = []

    if len(assits) == 0:
        input_kb.append(
            [InlineKeyboardButton(text="В данный момент не добавлено ассистентов", callback_data=f"undefind")]
        )

    else:
        for assist in assits:
            if assist.disable:
                continue
            if assist.only_for_premium == True and premium:
                input_kb.append(
                    [InlineKeyboardButton(text=f"{assist.title}", callback_data=f"assist_{assist.id}")]
                )
            else:
                input_kb.append(
                    [InlineKeyboardButton(text=f"🔒{assist.title}🔒", callback_data=f"assist_{assist.id}")]
                )

    kb = InlineKeyboardMarkup(
        inline_keyboard=input_kb,
    )
    return kb