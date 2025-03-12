from aiogram.fsm.state import StatesGroup, State


class TextState(StatesGroup):
    type = State()
    dialog = State()
    text = State()
