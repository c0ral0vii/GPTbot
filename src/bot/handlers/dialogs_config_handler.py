from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from more_itertools import chunked

from src.bot.keyboards.dialog_config_keyboard import dialog_config_keyboard
from src.bot.keyboards.select_gpt import paginate_models_dialogs
from src.db.orm.dialog_orm import DialogORM
from src.bot.states.dialog_state import DialogState

router = Router(name="dialog change router")


@router.callback_query(F.data == "configs_dialog")
async def dialog_configs_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик для выбора диалога для редактирования"""
    await callback.message.delete()

    data = await state.get_data()
    user_id = callback.from_user.id
    select_model = data.get("select_model")
    if not select_model:
        await callback.message.answer("Выберите модель для диалога")
        return
    
    dialogs = await DialogORM.get_dialogs(user_id=user_id, select_model=select_model)
    chunks = list(chunked(dialogs, 5))
    select_page = data.get("page", 1)
    
    await callback.message.answer(
        "Выберите диалог для редактирования:",
        reply_markup=await paginate_models_dialogs(
            callback="config_dialog_",
            page=select_page,
            max_pages=len(chunks),
            data=chunks[0],
            per_page=5,
            change_button=False,
        ),
    )
    await state.update_data(callback_text="config_dialog_", page=select_page, max_pages=len(chunks), change_button=False)


@router.callback_query(F.data.startswith("config_dialog_"))
async def select_dialog_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик для выбора диалога для редактирования"""
    await callback.message.delete()

    data = await state.get_data()
    dialog_id = callback.data.split("_")[-1]

    dialog = await DialogORM.get_dialog(dialog_id=int(dialog_id))

    if dialog:
        await callback.message.answer(
            f"Выберите действие для диалога:\n\n"
            f"Название диалога: {dialog.title}\n"
            f"Выберите действие:",
            reply_markup=await dialog_config_keyboard(dialog_id=dialog.id),
        )
    else:
        await callback.message.answer("Диалог не найден")


@router.callback_query(F.data.startswith("chg_"))
async def change_title_handler(callback: types.CallbackQuery, state: FSMContext):
    """Начало изменения названия диалога"""
    
    dialog_id = callback.data.split("_")[-1]
    await state.update_data(dialog_id=int(dialog_id))
    await callback.message.answer("Введите новое название для диалога(до 128 символов):")
    await state.set_state(DialogState.change_title)
    

@router.message(StateFilter(DialogState.change_title))
async def change_title(message: types.Message, state: FSMContext):
    """Изменение названия диалога"""
    if len(message.text) > 128:
        await message.answer("Название диалога не может быть больше 128 символов")
        return
    
    new_title = message.text[:127]
    data = await state.get_data()
    dialog_id = data.get("dialog_id")

    dialog = await DialogORM.get_dialog(dialog_id=int(dialog_id))
    if dialog:
        await message.delete()
        
        dialog.title = new_title
        await message.answer(f"Название диалога изменено на: {new_title}")
        await DialogORM.update_dialog(dialog_id=int(dialog_id), title=new_title)
    else:
        await message.answer("Диалог не найден")

    await state.clear()


@router.callback_query(F.data.startswith("delete_dialog_"))
async def delete_dialog(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик для удаления диалога"""
    dialog_id = callback.data.split("_")[-1]

    success = await DialogORM.delete_dialog(dialog_id=int(dialog_id))
    if success:
        await callback.message.answer("Диалог успешно удален.")
    else:
        await callback.message.answer("Ошибка: Диалог не найден или не может быть удален.")

    await callback.message.delete()


@router.callback_query(F.data == "return_to_dialog_selection")
async def return_to_dialog_selection(callback: types.CallbackQuery, state: FSMContext):
    """Возвращение к выбору диалога"""
    data = await state.get_data()
    user_id = callback.from_user.id
    select_model = data.get("select_model")

    if not select_model:
        await callback.message.answer("Выберите модель для диалога")
        return

    dialogs = await DialogORM.get_dialogs(user_id=user_id, select_model=select_model)
    chunks = list(chunked(dialogs, 5))
    select_page = data.get("page", 1)

    await callback.message.answer(
        "Выберите диалог для редактирования:",
        reply_markup=await paginate_models_dialogs(
            callback="config_dialog_",
            page=select_page,
            max_pages=len(chunks),
            data=chunks[0],
            per_page=5,
            change_button=False,
        ),
    )
    await state.update_data(callback_text="config_dialog_", page=select_page, max_pages=len(chunks), change_button=False)
