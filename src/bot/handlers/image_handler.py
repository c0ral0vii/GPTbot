from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from src.bot.keyboards.select_gpt import select_image_model, cancel_kb
from src.bot.states.image_state import ImageState
from src.db.orm.user_orm import PremiumUserORM
from src.scripts.queue.rabbit_queue import RabbitQueue
from src.utils.cached_user import _cached_user
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
        "Эти ИИ могут помочь с генерацией реалистичных фотографий по вашему тексту.\n\n"
        "💡 Выберите вашу модель для работы:",
        reply_markup=select_image_model(),
    )


@router.callback_query(F.data.startswith("select_"), StateFilter(ImageState.type))
async def select_image(callback: types.CallbackQuery, state: FSMContext):
    """Выбор модели"""

    gpt_select = callback.data.replace("select_", "")
    await callback.message.delete()
    priority = 0

    if settings.IMAGE_GPT.get(gpt_select):
        energy_cost = settings.IMAGE_GPT.get(gpt_select).get("energy_cost")
        select_model = settings.IMAGE_GPT.get(gpt_select).get("select_model")

        check_premium = await PremiumUserORM.is_premium_active(callback.from_user.id)

        if check_premium:
            priority = 5

        if check_premium and select_model.get("premium_free"):
            energy_cost = 0

    else:
        await callback.message.delete()
        await callback.message.answer(
            "Произошла ошибка при обнаружении модели!\n\nВозможно эта модель временно отключена!\nВы можете изменить ее в профиле")
        return

    await state.update_data(type_gpt=gpt_select, energy_cost=energy_cost, priority=priority)

    await callback.message.answer(
        f"Выбраная вами модель - {select_model}\n"
        f"Стоимость модели ⚡️ {energy_cost}\n\n"
        "Отправьте ваше сообщение для обработки:",
        reply_markup=await cancel_kb(),
    )

    await state.set_state(ImageState.text)


@router.message(F.text, StateFilter(ImageState.text))
async def handle_text(message: types.Message, state: FSMContext):
    """Генерация фотографий от миджорни"""

    data = await state.get_data()
    text = message.text
    key = f"{message.from_user.id}:generate"

    if await redis_manager.get(key):
        await message.answer("⚠️ Дождитесь завершения предыдущей генерации или оформите Premium, чтобы запускать несколько генераций одновременно. 👉 /premium")
        return

    answer_message = await message.answer("⏳ Подождите ваше сообщение в обработке...")

    await model.publish_message(
        queue_name=data.get("type_gpt"),
        message=text,
        user_id=message.from_user.id,
        answer_message=answer_message.message_id,
        energy_cost=data["energy_cost"],
        key=key,
        priority=data.get("priority", 0),
    )

    await redis_manager.set(key=key, value="generate")


@router.callback_query(F.data.startswith("refresh_"))
async def refresh_image(callback_data: types.CallbackQuery, state: FSMContext):
    """Кнопка refresh в боте"""

    image_id = callback_data.data.split("_")[-1]
    user_id = callback_data.from_user.id

    key = await _check_generation(callback_data)

    if key is False:
        return

    answer_message = await callback_data.message.answer(
        "⏳ Подождите ваше сообщение в обработке..."
    )
    state_data = await state.get_data()

    gpt_select = state_data["type_gpt"]

    if settings.IMAGE_GPT.get(gpt_select):
        energy_cost = settings.IMAGE_GPT.get(gpt_select).get("energy_cost")
    else:
        await callback_data.message.delete()
        await callback_data.message.answer(
            "Произошла ошибка при обнаружении модели!\n\nВозможно эта модель временно отключена!\nВы можете изменить ее в профиле")
        return

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

    await redis_manager.set(key=key, value="generate")


@router.callback_query(F.data.startswith("variation_"))
async def upscale_image(callback_data: types.CallbackQuery, state: FSMContext):
    """Кнопка Vi в боте"""

    image_id = callback_data.data.split("_")
    user_id = callback_data.from_user.id

    key = await _check_generation(callback_data)

    if key is False:
        return

    answer_message = await callback_data.message.answer(
        "⏳ Подождите ваше сообщение в обработке..."
    )
    data = await state.get_data()

    gpt_select = data["type_gpt"]

    if settings.IMAGE_GPT.get(gpt_select):
        energy_cost = settings.IMAGE_GPT.get(gpt_select).get("energy_cost")
    else:
        await callback_data.message.delete()
        await callback_data.message.answer(
            "Произошла ошибка при обнаружении модели!\n\nВозможно эта модель временно отключена!\nВы можете изменить ее в профиле")
        return


    await model.publish_message(
        queue_name="variation_midjourney",
        message="",
        user_id=user_id,
        answer_message=answer_message.message_id,
        energy_cost=energy_cost,
        choice=int(image_id[-2]),
        image_id=int(image_id[-1]),
        key=key,

        priority=data.get("priority", 0),
    )

    await redis_manager.set(key=key, value="generate")


@router.callback_query(F.data.startswith("upscale_"))
async def upscale_image(callback_data: types.CallbackQuery, state: FSMContext):
    """Кнопка Ui в боте"""

    image_id = callback_data.data.split("_")
    user_id = callback_data.from_user.id

    key = await _check_generation(callback_data)

    if key is False:
        return

    answer_message = await callback_data.message.answer(
        "⏳ Подождите ваше сообщение в обработке..."
    )
    data = await state.get_data()

    gpt_select = data["type_gpt"]

    if settings.IMAGE_GPT.get(gpt_select):
        energy_cost = settings.IMAGE_GPT.get(gpt_select).get("energy_cost")
    else:
        await callback_data.message.delete()
        await callback_data.message.answer(
            "Произошла ошибка при обнаружении модели!\n\nВозможно эта модель временно отключена!\nВы можете изменить ее в профиле")
        return

    await model.publish_message(
        queue_name="upscale_midjourney",
        message="",
        user_id=user_id,
        answer_message=answer_message.message_id,
        energy_cost=energy_cost,
        choice=int(image_id[-2]),
        image_id=int(image_id[-1]),
        key=key,

        priority=data.get("priority", 0),
    )

    await redis_manager.set(key=key, value="generate")


async def _check_generation(callback_data: types.CallbackQuery):
    user_id = callback_data.from_user.id
    key = f"{user_id}:generate"

    if await redis_manager.get(key):
        await callback_data.message.answer("⚠️ Дождитесь завершения предыдущей генерации или оформите Premium, чтобы запускать несколько генераций одновременно. 👉 /premium")
        return False
    return key
