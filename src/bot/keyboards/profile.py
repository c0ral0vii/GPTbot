from typing import Literal

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.config.config import settings
from src.db.enums_class import CLAUDEConfig, GPTConfig, MidjourneySpeedConfig
from src.db.orm.config_orm import ConfigORM


async def profile_settings_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Настройки пользователя"""

    settings_data = await ConfigORM.get_config(user_id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Chat GPT: {settings.TEXT_GPT.get(settings_data.gpt_select.value).get('select_model')}",
                    callback_data=f"change_chatgpt",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Claude: {settings.TEXT_GPT.get(settings_data.claude_select.value).get('select_model')}",
                    callback_data=f"change_claude",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Midjourney: {settings.IMAGE_GPT.get("midjourney", {}).get('speeds', {}).get(settings_data.midjourney_speed.value, {})["select_speed_name"]}",
                    callback_data=f"change_midjourney",
                )
            ],
        ],
    )

    return keyboard


async def change_settings_image_ai(
    user_id: int, model_type: Literal["midjourney"]
) -> InlineKeyboardMarkup:
    """Изменение настроек для ИИ которые работают с фотографиями"""
    buttons = []

    settings_data = await ConfigORM.get_config(user_id)
    if not settings_data:
        raise ValueError("Настройки пользователя не найдены")

    if model_type == "midjourney":
        selected_model = settings_data.midjourney_speed
        model_class = MidjourneySpeedConfig

    for model in model_class:
        model_config = settings.IMAGE_GPT.get("midjourney", {}).get("speeds")
        if not model_config or model_config.get("disable", False):
            continue

        button_text = model_config.get(model.value, {}).get(
            "select_speed_name", model.value
        )

        if selected_model == model:
            button_text = f"---> {button_text} <---"

        buttons.append(
            [
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"setting_{model_type}_{model.value}",
                )
            ]
        )

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    return kb


async def change_settings_text_ai(
    user_id: int, model_type: Literal["claude", "gpt"]
) -> InlineKeyboardMarkup:
    buttons = []

    # Получаем настройки пользователя
    settings_data = await ConfigORM.get_config(user_id)
    if not settings_data:
        raise ValueError("Настройки пользователя не найдены")

    # Определяем выбранную модель и класс модели
    if model_type == "claude":
        selected_model = settings_data.claude_select
        model_class = CLAUDEConfig
    elif model_type == "gpt":
        selected_model = settings_data.gpt_select
        model_class = GPTConfig
    else:
        raise ValueError("Неверный тип модели")

    for model in model_class:
        model_config = settings.TEXT_GPT.get(model.value)
        if not model_config or model_config.get("disable", False):
            continue

        button_text = model_config.get("select_model", model.value)

        # if model_config.get("premium_free"):
        #     if selected_model == model:
        #         button_text = f"---> {button_text} - ❗БЕСПЛАТНО С ПРЕМИУМ❗ <---"
        #     else:
        #         button_text = f"{button_text} - ❗БЕСПЛАТНО С ПРЕМИУМ❗"
        if selected_model == model:
            button_text = f"---> {button_text} <---"

        buttons.append(
            [
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"setting_{model_type}_{model.value}",
                )
            ]
        )

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    return kb
