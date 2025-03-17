
from aiogram import Router, F, types
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext

from src.bot.keyboards.select_gpt import get_models_dialogs, cancel_kb
from src.bot.states.text_state import GPTState
from src.db.orm.gpt_assistant_orm import GPTAssistantOrm
from src.bot.keyboards.gpt_assist_keyboard import gpt_assist_keyboard
from src.db.orm.user_orm import PremiumUserORM
from src.scripts.queue.rabbit_queue import model
from src.utils.redis_cache.redis_cache import redis_manager
from src.utils.text_scripts import _get_dialogs, _create_new_dialog, _get_dialog

router = Router()
ASSIST_START_TEXT = "Наши умные ассистенты помогут тебе с созданием контента, анализом трендов, генерацией идей и многим другим. Просто выбери подходящего и начни работать эффективнее!"
NOT_FOUND_ASSIST_TEXT = "В данный момент этот асистент отключен, выберите другого - /assistants"


@router.message(Command("assistants"))
@router.message(F.text == "🧑‍🔬 Ассистенты")
async def gpt_assist_handler(message: types.Message, state: FSMContext):
    """Хэндлер gpt assist"""

    assits = await GPTAssistantOrm.get_all_assistants()
    check_premium = await PremiumUserORM.is_premium_active(message.from_user.id)

    await message.answer(ASSIST_START_TEXT,
                         reply_markup=await gpt_assist_keyboard(assits, check_premium))
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
        await callback.message.answer("Для общения с ассистентами вам необходимо приобрести подписку /premium")
        return
    assist = await GPTAssistantOrm.get_select_assistants(int(gpt_select))

    if not assist or not assist.assistant_id or assist.disable:
        await callback.message.answer(NOT_FOUND_ASSIST_TEXT,)
        return

    energy_cost = assist.energy_cost

    priority = 0

    if check_premium:
        priority = 5
        energy_cost = 0

    await state.update_data(
        select_model=assist.title,
        energy_cost=float(energy_cost),
        type_gpt=assist.assistant_id,
        queue_select="gpt_assistant",
        priority=priority,
        comment=assist.comment if assist.comment else "-",
    )

    dialogs = await _get_dialogs(
        user_id=callback.from_user.id, select_model=assist.assistant_id
    )

    await callback.message.answer(
        f"Выбраная вами модель - {assist.title}\n"
        f"(поменять модель в настройках профиля)\n"
        f"Стоимость модели ⚡️ {energy_cost}\n\n"
        "Выберите прошлый диалог из списка ниже или создайте новый:",
        reply_markup=await get_models_dialogs(dialogs),
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
            user_id=callback.from_user.id, select_model=data["type_gpt"]
        )

        title = dialog.title
        await state.update_data(dialog_id=dialog.id)
    else:
        dialog = await _get_dialog(dialog_id=int(dialog_id))

        title = dialog.title
        await state.update_data(dialog_id=dialog_id)

    await callback.message.answer(
        f"Выбраная вами модель - {data["select_model"]}\n"
        f"(поменять модель в настройках профиля)\n"
        f"Стоимость модели ⚡️ {data["energy_cost"]}\n\n"
        f"Выбранный диалог: {title}\n\n"
        f"Коментарии по использованию: {data["comment"]}\n\n"
        "Напишите ваше сообщение ниже",
        reply_markup=await cancel_kb(),
    )

    await state.set_state(GPTState.text)

@router.message(F.text, StateFilter(GPTState.text))
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
        version=data.get("type_gpt"),
        message=text,
        user_id=message.from_user.id,
        answer_message=answer_message.message_id,
        energy_cost=data["energy_cost"],

        key=key,
        priority=data["priority"],
    )

    await redis_manager.set(key=key, value="generate", ttl=120)