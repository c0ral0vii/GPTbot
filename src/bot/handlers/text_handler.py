from aiogram import Router, types, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from more_itertools import chunked

from src.bot.keyboards.select_gpt import paginate_models_dialogs, select_text_gpt, cancel_kb, get_models_dialogs
from src.bot.states.text_state import TextState
from src.config.config import settings, EXCLUDE_PATTERN
from src.db.orm.user_orm import PremiumUserORM
from src.scripts.queue.rabbit_queue import model
from src.utils.logger import setup_logger
from src.utils.redis_cache.redis_cache import redis_manager
from src.utils.text_scripts import (
    _get_user_config_and_get_model,
    _get_dialogs,
    _create_new_dialog,
    _get_dialog,
)

router = Router()
logger = setup_logger(__name__)


@router.message(Command("text"))
@router.message(F.text == "💡 Chat GPT/Claude")
async def text_handler(message: types.Message, state: FSMContext):
    await message.answer(
        "Эти ИИ позволят вам придумать новые идеи, помочь вам в решении вопроса или написать статью, а может даже и написать код для приложения!\n\n"
        "💡 Выберите вашу модель для работы:",
        reply_markup=await select_text_gpt(),
    )
    await state.set_state(TextState.type)


@router.callback_query(F.data.startswith("select_"), StateFilter(TextState.type))
async def select_gpt(callback: types.CallbackQuery, state: FSMContext):
    gpt_select = callback.data.replace("select_", "")
    await callback.message.delete()

    user_model = await _get_user_config_and_get_model(
        user_id=callback.from_user.id, select_model=gpt_select
    )
    config_model = settings.TEXT_GPT.get(user_model.value)
    priority = 0

    if config_model:
        energy_cost = config_model.get("energy_cost")
        select_model = config_model.get("select_model")
        check_premium = await PremiumUserORM.is_premium_active(callback.from_user.id)

        if check_premium:
            priority = 5

        if check_premium and config_model.get("premium_free"):
            energy_cost = 0

    else:
        await callback.message.delete()
        await callback.message.answer(
            "Произошла ошибка при обнаружении модели!\n\nВозможно эта модель временно отключена!\nВы можете изменить ее в профиле"
        )
        return

    await state.update_data(
        select_model=user_model.value,
        energy_cost=energy_cost,
        type_gpt=select_model,
        queue_select=gpt_select,
        priority=priority,
    )

    dialogs = await _get_dialogs(
        user_id=callback.from_user.id, select_model=user_model.value
    )

    data = await state.get_data()

    if len(dialogs) <= 5:
        await callback.message.answer(
            f"Выбраная вами модель - {select_model}\n"
            f"(поменять модель в настройках профиля)\n"
            f"{f"Стоимость модели ⚡{data["energy_cost"]}" if data["energy_cost"] != 0 else ""}\n\n"
            "Выберите прошлый диалог из списка ниже или создайте новый:",
            reply_markup=await get_models_dialogs(dialogs),
        )
    else:
        per_page = 5
        chunks = list(chunked(dialogs, per_page))
        logger.debug(chunks)
        await state.update_data(
            page=1,
            max_pages=len(chunks),
        )
        
        await callback.message.answer(
            f"Выбраная вами модель - {select_model}\n"
            f"(поменять модель в настройках профиля)\n"
            f"{f"Стоимость модели ⚡{data["energy_cost"]}" if data["energy_cost"] != 0 else ""}\n\n"
            "Выберите прошлый диалог из списка ниже или создайте новый:",
            reply_markup=await paginate_models_dialogs(callback="dialog_", page=1, data=chunks[0], max_pages=len(chunks)),
        )

    await state.set_state(TextState.dialog)


@router.callback_query(F.data.startswith("page_"))
async def pages_handler(callback: types.CallbackQuery, state: FSMContext):
    """Страницы пагинации и их перелистывание"""
    user_id = callback.from_user.id
    action = callback.data.replace("page_", "")
    data = await state.get_data()
    select_model = data.get("select_model")
    if not select_model:
        await callback.message.answer("Изначально выберите версию ИИ в которой хотите посмотреть чаты")
        return
    
    dialogs = await _get_dialogs(
            user_id=user_id, select_model=select_model
        )
    chunks = list(chunked(dialogs, 5))
    select_page = data.get("page", 1)
    max_page = data.get("max_pages", 1)
    
    if action == "next":
        # Следующая страница
        if select_page == max_page:
            await callback.message.answer("Больше нет страниц спереди")   
            return
            
        select_page += 1
        
        await callback.message.edit_reply_markup(
            reply_markup=await paginate_models_dialogs(
                callback="dialog_",
                page=select_page,
                max_pages=max_page,
                data=chunks[select_page-1]
            )
        )
        await state.update_data(
            page=select_page
        ) 
        
    if action == "previous":
        # Предыдущая страница
        if select_page == 1:
            return
        
        select_page -= 1
        
        await callback.message.edit_reply_markup(
            reply_markup=await paginate_models_dialogs(
                callback="dialog_",
                page=select_page,
                max_pages=max_page,
                data=chunks[select_page-1]
            )
        )
        await state.update_data(
            page=select_page
        ) 
        
        
@router.callback_query(F.data.startswith("dialog_"), StateFilter(TextState.dialog))
async def select_dialog_handler(callback: types.CallbackQuery, state: FSMContext):
    dialog_select = callback.data.replace("dialog_", "")
    await callback.message.delete()
    data = await state.get_data()

    if dialog_select == "new":
        dialog = await _create_new_dialog(
            user_id=callback.from_user.id, select_model=data["select_model"]
        )

        title = dialog.title
        await state.update_data(dialog_id=dialog.id)
    else:
        dialog = await _get_dialog(dialog_id=int(dialog_select))

        title = dialog.title
        await state.update_data(dialog_id=dialog_select)

    await callback.message.answer(
        f"Выбраная вами модель - {data["select_model"]}\n"
        f"(поменять модель в настройках профиля)\n"
        f"{f"Стоимость модели ⚡{data["energy_cost"]}" if data["energy_cost"] != 0 else ""}\n\n"
        f"Выбранный диалог: {title}\n\n"
        "Напишите ваше сообщение ниже",
        reply_markup=await cancel_kb(),
    )

    await state.set_state(TextState.text)


@router.message(F.text.regexp(EXCLUDE_PATTERN), StateFilter(TextState.text))
async def text_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()

    text = message.text
    key = f"{message.from_user.id}:generate"

    if await redis_manager.get(key):
        await message.delete()
        await message.answer("⚠️ Дождитесь завершения предыдущей генерации")
        return

    answer_message = await message.answer("⏳ Подождите ваше сообщение в обработке...")

    await model.publish_message(
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


@router.message(F.document, StateFilter(TextState.text))
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

    key = f"{message.from_user.id}:generate"

    if await redis_manager.get(key):
        await message.delete()
        await message.answer("⚠️ Дождитесь завершения предыдущей генерации")
        return

    file_url = f"https://api.telegram.org/file/bot{settings.BOT_API}/{file.file_path}"
    answer_message = await message.answer(f"📂 Файл `{file_name}` обрабатывается...")

    await model.publish_message(
        queue_name=data.get("queue_select"),
        dialog_id=int(data.get("dialog_id")),
        version=data.get("select_model"),
        file={"url": file_url, "name": file_name, "type": "document"},
        user_id=message.from_user.id,
        answer_message=answer_message.message_id,
        energy_cost=data["energy_cost"],
        key=key,
        priority=data["priority"],
    )
    await redis_manager.set(key=key, value="generate", ttl=120)
