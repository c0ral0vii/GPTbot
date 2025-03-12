from aiogram import Router, types, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.select_gpt import select_text_gpt, cancel_kb, get_models_dialogs
from src.bot.states.text_state import TextState
from src.config.config import settings
from src.db.enums_class import GPTConfig, CLAUDEConfig
from src.db.orm.config_orm import ConfigORM
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
        reply_markup=select_text_gpt(),
    )
    await state.set_state(TextState.type)


@router.callback_query(F.data.startswith("select_"), StateFilter(TextState.type))
async def select_gpt(callback: types.CallbackQuery, state: FSMContext):
    gpt_select = callback.data.replace("select_", "")
    await callback.message.delete()
    user_model = await _get_user_config_and_get_model(
        user_id=callback.from_user.id, select_model=gpt_select
    )
    select_model = settings.TEXT_GPT.get(user_model.value)

    if select_model:
        energy_cost = select_model.get("energy_cost")
        select_model = select_model.get("select_model")
    else:
        energy_cost = 1
        select_model = gpt_select

    await state.update_data(
        select_model=user_model.value,
        energy_cost=energy_cost,
        type_gpt=select_model,
        queue_select=gpt_select,
    )

    dialogs = await _get_dialogs(
        user_id=callback.from_user.id, select_model=user_model.value
    )

    await callback.message.answer(
        f"Выбраная вами модель - {select_model}\n"
        f"Стоимость модели ⚡️ {energy_cost}\n\n"
        "Выберите прошлый диалог из списка ниже или создайте новый:",
        reply_markup=await get_models_dialogs(dialogs),
    )

    await state.set_state(TextState.dialog)


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
        f"Стоимость модели ⚡️ {data["energy_cost"]}\n\n"
        f"Выбранный диалог: {title}\n\n"
        "Напишите ваше сообщение ниже",
        reply_markup=await cancel_kb(),
    )

    await state.set_state(TextState.text)


@router.message(F.text, StateFilter(TextState.text))
async def text_handler(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()

    text = message.text
    key = f"{message.from_user.id}:generate"

    if await redis_manager.get(key):
        await message.delete()
        await message.answer("⏳ Подождите пока идет генерация.")
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
        priority=0,
    )

    await redis_manager.set(key=key, value="generate")
