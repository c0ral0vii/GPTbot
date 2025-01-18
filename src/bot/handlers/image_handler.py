from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from src.bot.keyboards.select_gpt import select_image_model, cancel_kb
from src.bot.states.image_state import ImageState
from src.scripts.queue.rabbit_queue import RabbitQueue
from src.utils.redis_cache.redis_cache import redis_manager

model = RabbitQueue()

router = Router()


@router.message(Command("image"))
@router.message(F.text == "🌄 MidJourney")
async def handle_image(message: types.Message, state: FSMContext):
    await state.set_state(ImageState.type)
    await message.answer(
        "Эти ИИ могут помочь с генерацией реалистичных фотографий только по вашему тексту.\n\n"
        "💡 Выберите вашу модель для работы:",
        reply_markup=select_image_model()
    )


@router.callback_query(F.data.startswith("select_"), StateFilter(ImageState.type))
async def select_image(callback: types.CallbackQuery, state: FSMContext):
    gpt_select = callback.data.replace("select_", "")
    await callback.message.delete()

    if gpt_select == "midjourney":
        energy_cost = 1
        select_model = "Midjourney"
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


