from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from src.bot.keyboards.select_gpt import select_image_model, cancel_kb
from src.bot.states.image_state import ImageState
from src.scripts.queue.rabbit_queue import RabbitQueue
from src.utils.logger import setup_logger
from src.utils.redis_cache.redis_cache import redis_manager
from src.config.config import settings


model = RabbitQueue()

router = Router()
logger = setup_logger(__name__)


@router.message(Command("image"))
@router.message(F.text == "🌄 MidJourney")
async def handle_image(message: types.Message, state: FSMContext):
    await state.set_state(ImageState.type)
    await message.answer(
        "Эти ИИ могут помочь с генерацией реалистичных фотографий только по вашему тексту.\n\n"
        "💡 Выберите вашу модель для работы:",
        reply_markup=select_image_model(),
    )


@router.callback_query(F.data.startswith("select_"), StateFilter(ImageState.type))
async def select_image(callback: types.CallbackQuery, state: FSMContext):
    gpt_select = callback.data.replace("select_", "")
    await callback.message.delete()

    if settings.IMAGE_GPT.get(gpt_select):
        energy_cost = settings.IMAGE_GPT.get(gpt_select).get("energy_cost")
        select_model = settings.IMAGE_GPT.get(gpt_select).get("select_model")
    else:
        energy_cost = 1
        select_model = gpt_select

    await state.update_data(type_gpt=gpt_select, energy_cost=energy_cost)

    await callback.message.answer(
        f"Выбраная вами модель - {select_model}\n"
        f"Стоимость модели ⚡️ {energy_cost}\n\n"
        "Отправьте ваше сообщение для обработки:",
        reply_markup=cancel_kb(),
    )

    await state.set_state(ImageState.text)


@router.message(F.text, StateFilter(ImageState.text))
async def handle_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    text = message.text
    key = f"{message.from_user.id}:generate"

    if await redis_manager.get(key):
        await message.answer("⏳ Подождите пока идет генерация.")
        return

    answer_message = await message.answer("⏳ Подождите ваше сообщение в обработке...")

    await model.publish_message(
        queue_name=data.get("type_gpt"),
        message=text,
        user_id=message.from_user.id,
        answer_message=answer_message.message_id,
        energy_cost=data["energy_cost"],
        key=key,
    )

    await redis_manager.set(key=key, value="generate")


@router.callback_query(F.data.startswith("refresh_"))
async def refresh_image(callback_data: types.CallbackQuery, state: FSMContext):
    logger.debug(callback_data.data)
    image_id = callback_data.data.split("_")[-1]
    user_id = callback_data.from_user.id
    key = f"{user_id}:generate"

    if await redis_manager.get(key):
        await callback_data.message.answer("⏳ Подождите пока идет генерация.")
        return

    answer_message = await callback_data.message.answer("⏳ Подождите ваше сообщение в обработке...")
    state_data = await state.get_data()

    gpt_select = state_data["type_gpt"]

    if settings.IMAGE_GPT.get(gpt_select):
        energy_cost = settings.IMAGE_GPT.get(gpt_select).get("energy_cost")
        select_model = settings.IMAGE_GPT.get(gpt_select).get("select_model")
    else:
        energy_cost = 1
        select_model = gpt_select
    logger.debug(image_id)
    await model.publish_message(
        queue_name="refresh_midjourney",
        message="",
        user_id=user_id,
        answer_message=answer_message.message_id,
        energy_cost=energy_cost,
        image_id=int(image_id),

        key=key,
    )
