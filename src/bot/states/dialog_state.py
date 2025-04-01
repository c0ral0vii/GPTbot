from aiogram.fsm.state import State, StatesGroup

class DialogState(StatesGroup):
    change_title = State()