from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from src.bot.keyboards.select_gpt import select_image_model, cancel_kb
from src.bot.states.image_state import ImageState
from src.scripts.queue.rabbit_queue import RabbitQueue


model = RabbitQueue()

router = Router()


@router.message(Command("image"))
async def handle_image(message: types.Message, state: FSMContext):
    await state.set_state(ImageState.type)
    await message.answer(
        "Выбери искуственный интелект для обработки:", reply_markup=select_image_model()
    )


@router.callback_query(F.data.startswith("select_"), StateFilter(ImageState.type))
async def select_image(callback: types.CallbackQuery, state: FSMContext):
    gpt_select = callback.data.replace("select_", "")
    await state.update_data(type_gpt=gpt_select)
    await callback.message.delete()
    await callback.message.answer(
        "Отправьте текст для генерации:", reply_markup=cancel_kb()
    )

    await state.set_state(ImageState.text)


@router.message(F.text, StateFilter(ImageState.text))
async def handle_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    text = message.text
    answer_message = await message.answer("⏳ Подождите ваше сообщение в обработке...")

    await model.publish_message(
        queue_name=data.get("type_gpt"),
        message=text,
        user_id=message.from_user.id,
        answer_message=answer_message.message_id,
    )
