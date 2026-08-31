from aiogram.fsm.state import State, StatesGroup


class CategorySearchState(StatesGroup):
    waiting_for_query: State = State()


class GlobalSearchState(StatesGroup):
    waiting_for_query: State = State()
    waiting_for_ingredients: State = State()
