import re
from typing import Any, Optional

from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from dotenv.variables import Literal

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

EXCLUDE_PATTERN = re.compile(r"^/.*|💡 Chat GPT/Claude", re.IGNORECASE)

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

        if check_premium and settings.IMAGE_GPT.get(gpt_select).get("premium_free"):
            energy_cost = 0

    else:
        await callback.message.delete()
        await callback.message.answer(
            "Произошла ошибка при обнаружении модели!\n\nВозможно эта модель временно отключена!\nВы можете изменить ее в профиле"
        )
        return

    await state.update_data(
        type_gpt=gpt_select, energy_cost=energy_cost, priority=priority
    )

    await callback.message.answer(
        f"Выбраная вами модель - {select_model}\n"
        f"Стоимость модели ⚡️ {energy_cost}\n\n"
        "Отправьте ваше сообщение для обработки:",
        reply_markup=await cancel_kb(),
    )

    await state.set_state(ImageState.text)


@router.message(StateFilter(ImageState.text), F.text.regexp(r"^(?!/.*|💡 Chat GPT/Claude$).+"))
async def handle_text(message: types.Message, state: FSMContext):
    """Генерация фотографий от миджорни"""

    data = await state.get_data()
    text = message.text
    key = await check_generation(message, data.get("priority", 0))

    if key is False:
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

    await add_generate(message, data.get("priority", 0))


@router.callback_query(F.data.startswith("refresh_"))
async def refresh_image(callback_data: types.CallbackQuery, state: FSMContext):
    """Кнопка refresh в боте"""

    image_id = callback_data.data.split("_")[-1]
    user_id = callback_data.from_user.id
    data = await state.get_data()

    key = await check_generation(callback_data, data.get("priority", 0))

    if key is False:
        return

    answer_message = await callback_data.message.answer(
        "⏳ Подождите ваше сообщение в обработке..."
    )

    gpt_select = data["type_gpt"]

    if settings.IMAGE_GPT.get(gpt_select):
        energy_cost = settings.IMAGE_GPT.get(gpt_select).get("energy_cost")
    else:
        await callback_data.message.delete()
        await callback_data.message.answer(
            "Произошла ошибка при обнаружении модели!\n\nВозможно эта модель временно отключена!\nВы можете изменить ее в профиле"
        )
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

        priority=data.get("priority", 0),
    )

    await add_generate(callback_data, data.get("priority", 0))


@router.callback_query(F.data.startswith("variation_"))
async def upscale_image(callback_data: types.CallbackQuery, state: FSMContext):
    """Кнопка Vi в боте"""

    image_id = callback_data.data.split("_")
    user_id = callback_data.from_user.id
    data = await state.get_data()

    key = await check_generation(callback_data, data.get("priority", 0))

    if key is False:
        return

    answer_message = await callback_data.message.answer(
        "⏳ Подождите ваше сообщение в обработке..."
    )

    gpt_select = data["type_gpt"]

    if settings.IMAGE_GPT.get(gpt_select):
        energy_cost = settings.IMAGE_GPT.get(gpt_select).get("energy_cost")
    else:
        await callback_data.message.delete()
        await callback_data.message.answer(
            "Произошла ошибка при обнаружении модели!\n\nВозможно эта модель временно отключена!\nВы можете изменить ее в профиле"
        )
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

    await add_generate(callback_data, data.get("priority", 0))


@router.callback_query(F.data.startswith("upscale_"))
async def upscale_image(callback_data: types.CallbackQuery, state: FSMContext):
    """Кнопка Ui в боте"""

    image_id = callback_data.data.split("_")
    user_id = callback_data.from_user.id
    data = await state.get_data()

    key = await check_generation(callback_data, data.get("priority", 0))

    if key is False:
        return

    answer_message = await callback_data.message.answer(
        "⏳ Подождите ваше сообщение в обработке..."
    )

    gpt_select = data["type_gpt"]

    if settings.IMAGE_GPT.get(gpt_select):
        energy_cost = settings.IMAGE_GPT.get(gpt_select).get("energy_cost")
    else:
        await callback_data.message.delete()
        await callback_data.message.answer(
            "Произошла ошибка при обнаружении модели!\n\nВозможно эта модель временно отключена!\nВы можете изменить ее в профиле"
        )
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

    await add_generate(callback_data, data.get("priority", 0))


async def check_generation(data: types.CallbackQuery | types.Message, priority: int) -> Optional[str]:
    user_id = data.from_user.id
    key_prefix = f"{user_id}:generate:image"
    logger.debug(user_id)

    status = await redis_manager.get(key=key_prefix)
    if isinstance(status, dict):
        if status["max_generate"] == status["active_generate"]:
            await user_wait(data, status["max_generate"])
            return False

    if status is None:
        user_data = {
            "max_generate": 2 if priority == 5 else 1,
            "active_generate": 0,
        }

        await redis_manager.set(key=key_prefix, value=user_data, ttl=3600)
        return key_prefix
    else:
        return key_prefix


PREMIUM_TEXT = "⚠️ Дождитесь завершения ваших генераций"
NOT_PREMIUM_TEXT = "⚠️ Дождитесь завершения предыдущей генерации или оформите Premium, чтобы запускать несколько генераций одновременно. 👉 /premium"

async def user_wait(data, counts: int = 2) -> None:
    if isinstance(data, types.CallbackQuery):
        if counts == 1:
            await data.message.answer(NOT_PREMIUM_TEXT)
        else:
            await data.message.answer(PREMIUM_TEXT)
    if isinstance(data, types.Message):
        if counts == 1:
            await data.answer(NOT_PREMIUM_TEXT)
        else:
            await data.answer(PREMIUM_TEXT)


async def add_generate(data: types.CallbackQuery | types.Message, priority: int):
    """Добавление генерации в кэш"""

    user_id = data.from_user.id
    key_prefix = f"{user_id}:generate:image"

    status = await redis_manager.get(key=key_prefix)
    if priority == 5 and status["max_generate"] == 1:
        status["max_generate"] = 2
        await redis_manager.set(key=key_prefix, value=status, ttl=3600)

    if priority == 0 and status["max_generate"] == 2:
        status["max_generate"] = 1
        await redis_manager.set(key=key_prefix, value=status, ttl=3600)

    if status:
        if status["max_generate"] == status["active_generate"]:
            await user_wait(data, status["max_generate"])
            return False
        else:
            status["active_generate"] += 1
            await redis_manager.set(key=key_prefix, value=status, ttl=3600)
            return True
    else:
        await check_generation(data, priority)