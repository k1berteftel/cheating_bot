from aiogram.fsm.state import State, StatesGroup

# Обычная группа состояний


class startSG(StatesGroup):
    start = State()
    get_channel = State()
    get_volume = State()
    get_male = State()
    get_date = State()
    get_time = State()
    confirm_task = State()
    deferred_tasks_menu = State()
