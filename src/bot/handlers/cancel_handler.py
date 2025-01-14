from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

router = Router()


@router.callback_query(F.data == "cancel")
async def cancel_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        "Отмена произошла, выберите следующие действия", reply_markup=None
    )

    await state.clear()
