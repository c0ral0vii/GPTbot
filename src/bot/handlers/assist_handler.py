from aiogram import Router, F, types, Bot
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from more_itertools import chunked

from src.bot.keyboards.select_gpt import (
    change_dialog_kb,
    get_models_dialogs,
    cancel_kb,
    paginate_models_dialogs,
)
from src.bot.states.text_state import GPTState
from src.config.config import EXCLUDE_PATTERN, settings
from src.db.orm.gpt_assistant_orm import GPTAssistantOrm
from src.bot.keyboards.gpt_assist_keyboard import gpt_assist_keyboard
from src.db.orm.user_orm import PremiumUserORM
from src.scripts.queue.rabbit_queue import model
from src.utils.redis_cache.redis_cache import redis_manager
from src.utils.text_scripts import _get_dialogs, _create_new_dialog, _get_dialog

router = Router()
ASSIST_START_TEXT = "Наши умные ассистенты помогут тебе с созданием контента, анализом трендов, генерацией идей и многим другим. Просто выбери подходящего и начни работать эффективнее!"
NOT_FOUND_ASSIST_TEXT = (
    "В данный момент этот асистент отключен, выберите другого - /assistants"
)


@router.message(Command("assistants"))
@router.message(F.text == "🧑‍🔬 Ассистенты")
async def gpt_assist_handler(message: types.Message, state: FSMContext):
    """Хэндлер gpt assist"""

    assits = await GPTAssistantOrm.get_all_assistants()
    check_premium = await PremiumUserORM.is_premium_active(message.from_user.id)

    await message.answer(
        ASSIST_START_TEXT, reply_markup=await gpt_assist_keyboard(assits, check_premium)
    )
    await state.set_state(GPTState.assist)
    await state.update_data(
        premium=check_premium,
    )


@router.callback_query(F.data.startswith("assist_"), StateFilter(GPTState.assist))
async def select_gpt(callback: types.CallbackQuery, state: FSMContext):
    gpt_select = callback.data.replace("assist_", "")
    await callback.message.delete()
    data = await state.get_data()
    check_premium = data["premium"]
    if not check_premium:
        await callback.message.answer(
            "👨‍💻 Ассистенты недоступны.\n\n"
            "🚨 Для работы с ассистентами нужен PRO-доступ!\n\n"
            "🔓 Оформи PRO и получи:\n"
            "✅ Безлимитный доступ ко всем ассистентам\n"
            "⚡ +2500 энергии – работай больше, зарабатывай быстрее\n"
            "🚀 Приоритетную скорость обработки запросов\n"
            "🔐 Эксклюзивные инструменты и функции\n",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="💳 РАЗБЛОКИРОВАТЬ PRO", callback_data="/PRO"
                        ),
                    ],
                ]
            ),
        )
        return

    assist = await GPTAssistantOrm.get_select_assistants(int(gpt_select))

    if not assist or not assist.assistant_id or assist.disable:
        await callback.message.answer(
            NOT_FOUND_ASSIST_TEXT,
        )
        return

    energy_cost = assist.energy_cost

    priority = 0

    if check_premium:
        priority = 5
        energy_cost = 0

    await state.update_data(
        assist_title=assist.title,
        select_model=assist.assistant_id,
        energy_cost=float(energy_cost),
        queue_select="gpt_assistant",
        priority=priority,
        comment=assist.comment if assist.comment else "-",
    )

    dialogs = await _get_dialogs(
        user_id=callback.from_user.id, select_model=assist.assistant_id
    )
    data = await state.get_data()
    if len(dialogs) <= 5:
        await callback.message.answer(
            f"Выбраный вами ассистент - {data["assist_title"]}\n"
            f"{f"Стоимость модели ⚡{data["energy_cost"]}" if data["energy_cost"] != 0 else ""}\n\n"
            "Выберите прошлый диалог из списка ниже или создайте новый:",
            reply_markup=await get_models_dialogs(dialogs),
        )
    else:
        per_page = 5
        chunks = list(chunked(dialogs, per_page))
        await state.update_data(
            page=1,
            max_pages=len(chunks),
        )

        await callback.message.answer(
            f"Выбраный вами ассистент - {data["assist_title"]}\n"
            f"{f"Стоимость модели ⚡{data["energy_cost"]}" if data["energy_cost"] != 0 else ""}\n\n"
            "Выберите прошлый диалог из списка ниже или создайте новый:",
            reply_markup=await paginate_models_dialogs(
                callback="dialog_", page=1, data=chunks[0], max_pages=len(chunks)
            ),
        )

    await state.set_state(GPTState.dialog)


@router.callback_query(F.data.startswith("dialog_"), StateFilter(GPTState.dialog))
async def select_dialog(callback: types.CallbackQuery, state: FSMContext):
    dialog_id = callback.data.replace("dialog_", "")
    user_id = callback.from_user.id
    await callback.message.delete()
    data = await state.get_data()

    if dialog_id == "new":
        dialog = await _create_new_dialog(
            user_id=callback.from_user.id, select_model=data["select_model"]
        )

        title = dialog.title
        await state.update_data(dialog_id=dialog.id)
    else:
        dialog = await _get_dialog(dialog_id=int(dialog_id))

        title = dialog.title
        await state.update_data(dialog_id=dialog_id)

    await callback.message.answer(
        f"Выбраный вами ассистент - {data["assist_title"]}\n"
        f"{f"Стоимость модели ⚡{data["energy_cost"]}" if data["energy_cost"] != 0 else ""}\n\n"
        f"Выбранный диалог: {title}\n\n"
        f"Коментарии по использованию: {data["comment"]}\n\n"
        "Напишите ваше сообщение ниже",
        reply_markup=await change_dialog_kb(dialog_id=dialog.id),
    )

    await state.set_state(GPTState.text)


@router.message(F.text.regexp(EXCLUDE_PATTERN), StateFilter(GPTState.text))
async def text_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()

    text = message.text
    key = f"{message.from_user.id}:generate"

    if await redis_manager.get(key):
        await message.delete()
        await message.answer("⚠️ Дождитесь завершения предыдущей генерации")
        return

    answer_message = await message.answer("⏳ Подождите ваше сообщение в обработке...")

    await _publish_message(
        queue_name=data.get("queue_select"),
        dialog_id=int(data.get("dialog_id")),
        version=data.get("select_model"),
        message=text,
        user_id=message.from_user.id,
        answer_message=answer_message.message_id,
        energy_cost=data["energy_cost"],
        key=key,
        priority=data["priority"],
    )

    await redis_manager.set(key=key, value="generate", ttl=120)


@router.message(F.document, StateFilter(GPTState.text))
async def file_handler(message: types.Message, state: FSMContext, bot: Bot):
    """Обработчик документов"""
    data = await state.get_data()

    file_id = message.document.file_id
    file_name = message.document.file_name
    file = await bot.get_file(file_id)
    allowed_extensions = {".txt", ".csv", ".html"}
    if not any(file_name.endswith(ext) for ext in allowed_extensions):
        await message.answer("⚠️ Поддерживаются только файлы .txt, .csv, .html!")
        return

    file_url = f"https://api.telegram.org/file/bot{settings.BOT_API}/{file.file_path}"
    answer_message = await message.answer(f"📂 Файл `{file_name}` обрабатывается...")

    await _publish_message(
        queue_name=data.get("queue_select"),
        dialog_id=int(data.get("dialog_id")),
        version=data.get("select_model"),
        message=message.caption,
        file={"url": file_url, "name": file_name, "type": "document"},
        user_id=message.from_user.id,
        answer_message=answer_message.message_id,
        energy_cost=data["energy_cost"],
        key=f"{message.from_user.id}:generate",
        priority=data["priority"],
    )


@router.message(F.voice, StateFilter(GPTState.text))
async def voice_handler(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()

    voice = message.voice
    file = await bot.get_file(voice.file_id)

    key = f"{message.from_user.id}:generate"
    if await redis_manager.get(key):
        await message.delete()
        await message.answer("⚠️ Дождитесь завершения предыдущей генерации")
        return

    file_url = f"https://api.telegram.org/file/bot{settings.BOT_API}/{file.file_path}"
    answer_message = await message.answer("🎙 Обработка голосового сообщения...")

    await _publish_message(
        queue_name=data.get("queue_select"),
        dialog_id=int(data.get("dialog_id")),
        version=data.get("select_model"),
        file={"url": file_url, "type": "voice"},
        user_id=message.from_user.id,
        answer_message=answer_message.message_id,
        energy_cost=data["energy_cost"],
        key=key,
        priority=data["priority"],
    )

    await redis_manager.set(key=key, value="generate", ttl=120)



async def _publish_message(**kwargs):
    await model.publish_message(**kwargs)
