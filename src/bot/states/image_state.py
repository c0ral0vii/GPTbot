from aiogram.fsm.state import StatesGroup, State


class ImageState(StatesGroup):
    type = State()

    text = State()
