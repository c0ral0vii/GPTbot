from aiogram import Router, types, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from src.bot.keyboards.select_gpt import select_text_gpt, cancel_kb
from src.bot.states.text_state import TextState
from src.scripts.queue.rabbit_queue import model


router = Router()


@router.message(Command("text"))
@router.message(F.text == "💡 Chat GPT/Claude")
async def text_handler(message: types.Message, state: FSMContext):
    await message.answer(
        "Эти ИИ позволят вам придумать новые идеи, помочь вам в решении вопроса или написать статью!\n\n"
        "💡 Выберите вашу модель для работы:",
        reply_markup=select_text_gpt(),
    )
    await state.set_state(TextState.type)


@router.callback_query(F.data.startswith("select_"), StateFilter(TextState.type))
async def select_gpt(callback: types.CallbackQuery, state: FSMContext):
    gpt_select = callback.data.replace("select_", "")
    await callback.message.delete()
    if gpt_select == "chat_gpt":
        energy_cost = 0.5
        select_model = "Chat GPT"
    elif gpt_select == "claude":
        energy_cost = 0.7
        select_model = "Claude"
    else:
        energy_cost = 1
        select_model = "Не выбрано"


    await state.update_data(type_gpt=gpt_select, energy_cost=energy_cost)

    await callback.message.answer(
        f"Выбраная вами модель - #{select_model}\n" 
        f"Стоимость модели ⚡️ {energy_cost}\n\n"
        "Отправьте ваше сообщение для обработки:",

        reply_markup=cancel_kb(),
    )

    await state.set_state(TextState.text)


@router.message(F.text, StateFilter(TextState.text))
async def text_handler(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    text = message.text
    answer_message = await message.answer("⏳ Подождите ваше сообщение в обработке...")

    await model.publish_message(
        queue_name=data.get("type_gpt"),
        message=text,
        user_id=message.from_user.id,
        answer_message=answer_message.message_id,
        energy_cost=data["energy_cost"],
    )