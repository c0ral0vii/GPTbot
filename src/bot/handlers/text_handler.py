from aiogram import Router, types, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from src.bot.keyboards.select_gpt import select_text_gpt, cancel_kb
from src.bot.states.text_state import TextState
from src.config.config import settings
from src.scripts.queue.rabbit_queue import model
from src.utils.logger import setup_logger
from src.utils.redis_cache.redis_cache import redis_manager


router = Router()
logger = setup_logger(__name__)


@router.message(Command("text", "code"))
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

    if settings.TEXT_GPT.get(gpt_select):
        energy_cost = settings.TEXT_GPT.get(gpt_select).get("energy_cost")
        select_model = settings.TEXT_GPT.get(gpt_select).get("select_model")
    else:
        energy_cost = 1
        select_model = gpt_select

    await state.update_data(
        type_gpt=gpt_select, energy_cost=energy_cost, bot_message=None
    )

    await callback.message.answer(
        f"Выбраная вами модель - {select_model}\n"
        f"Стоимость модели ⚡️ {energy_cost}\n\n"
        "Отправьте ваше сообщение для обработки:",
        reply_markup=cancel_kb(),
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
    if data["bot_message"]:
        await model.publish_message(
            queue_name=data.get("type_gpt"),
            message=text,
            last_message=data["bot_message"],
            user_id=message.from_user.id,
            answer_message=answer_message.message_id,
            energy_cost=data["energy_cost"],
            key=key,
        )
        await state.update_data(bot_message=None)
    else:
        await model.publish_message(
            queue_name=data.get("type_gpt"),
            message=text,
            user_id=message.from_user.id,
            answer_message=answer_message.message_id,
            energy_cost=data["energy_cost"],
            key=key,
        )

    await redis_manager.set(key=key, value="generate")


@router.callback_query(F.data == "upgrade_message")
async def upgrade_message(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.message.answer(
        "Отправьте сообщение для доработки:", reply_markup=cancel_kb()
    )

    await state.update_data(bot_message=callback.message.text)
