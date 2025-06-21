from aiogram.fsm.state import State, StatesGroup

# Обычная группа состояний


class startSG(StatesGroup):
    start = State()
    cheating_menu = State()
    account_choose = State()
    get_login = State()
    get_password = State()
    get_account_name = State()
    del_account = State()
    get_channel = State()
    get_volume = State()
    get_male = State()
    get_date = State()
    get_time = State()
    confirm_task = State()
    tasks_menu = State()
    disable_task = State()
    job_menu = State()
