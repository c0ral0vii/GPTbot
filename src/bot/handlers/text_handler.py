import json
from aiogram import Router, types, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from src.bot.keyboards.select_gpt import select_text_gpt, cancel_kb
from src.bot.states.text_state import TextState
from src.utils.queue.rabbit_queue import RabbitQueue


router = Router()


@router.message(Command("text"))
async def text_handler(message: types.Message, state: FSMContext):
    await message.answer(
        "Выберите вашу модель для работы:", reply_markup=select_text_gpt()
    )
    await state.set_state(TextState.type)


@router.callback_query(F.data.startswith("select_"), StateFilter(TextState.type))
async def select_gpt(callback: types.CallbackQuery, state: FSMContext):
    gpt_select = callback.data.replace("select_", "")
    await state.update_data(type_gpt=gpt_select)

    await callback.message.answer(
        f"Выбраная вами модель - {gpt_select}\n\nОтправьте ваш текст:",
        reply_markup=cancel_kb(),
    )
    await state.set_state(TextState.text)


@router.message(F.text, StateFilter(TextState.text))
async def text_handler(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    text = message.text
    answer_message = await message.answer("⏳ Подождите ваше сообщение в обработке...")

    await RabbitQueue.publish_message(
        queue_name=data.get("type_gpt"),
        message=text,
        answer_message=answer_message,
    )

