from aiogram.fsm.state import State, StatesGroup


class ParseState(StatesGroup):
    waiting_genre = State()
