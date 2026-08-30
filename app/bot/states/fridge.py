from aiogram.fsm.state import State, StatesGroup


class FridgeInputState(StatesGroup):
    waiting_for_items_add: State = State()
    waiting_for_items_replace: State = State()
