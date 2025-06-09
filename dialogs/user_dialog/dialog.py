from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import SwitchTo, Column, Row, Button, Group, Select, Start, Url, Calendar
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.media import DynamicMedia

from dialogs.user_dialog import getters

from states.state_groups import startSG

user_dialog = Dialog(
    Window(
        Const('Главное меню'),
        Column(
            SwitchTo(Const('Выбрать аккаунт'), id='choose_account_switcher', state=startSG.account_choose),
        ),
        state=startSG.start
    ),
    Window(
        Const('Выберите аккаунт, на который вы хотели бы зайти'),
        Column(
            Select(
                Format('{item[0]}'),
                id='accounts_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.choose_account
            ),
        ),
        SwitchTo(Const('Назад'), id='back', state=startSG.start),
        getter=getters.choose_account_getter,
        state=startSG.account_choose
    ),
    Window(
        Const('Главное меню'),
        Column(
            SwitchTo(Const('Начать накрутку'), id='get_channel_switcher', state=startSG.get_channel),
            SwitchTo(Const('Отложенные задачи'), id='deferred_tasks_menu', state=startSG.tasks_menu),
        ),
        SwitchTo(Const('Назад'), id='back', state=startSG.start),
        state=startSG.cheating_menu
    ),
    Window(
        Const('Список отложенных задач:'),
        Format('{jobs}'),
        SwitchTo(Const('Отключить задачу'), id='disable_task_switcher', state=startSG.disable_task),
        SwitchTo(Const('Назад'), id='back_cheating_menu', state=startSG.cheating_menu),
        getter=getters.tasks_menu_getter,
        state=startSG.tasks_menu
    ),
    Window(
        Const('Выберите задачу, которую вы хотели бы удалить'),
        Column(
            Select(
                Format('{item[0]}'),
                id='jobs_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.choose_job_del
            ),
        ),
        SwitchTo(Const('Назад'), id='back_tasks_menu', state=startSG.tasks_menu),
        getter=getters.disable_task_getter,
        state=startSG.disable_task
    ),
    Window(
        Const('Введите ссылку на канал'),
        TextInput(
            id='get_channel',
            on_success=getters.get_channel
        ),
        SwitchTo(Const('Назад'), id='back_cheating_menu', state=startSG.cheating_menu),
        state=startSG.get_channel
    ),
    Window(
        Const('Введите общее кол-во человек для накрутки'),
        TextInput(
            id='get_volume',
            on_success=getters.get_volume
        ),
        SwitchTo(Const('Назад'), id='back_get_channel', state=startSG.get_channel),
        state=startSG.get_volume
    ),
    Window(
        Const('Укажите пол заливаемой аудитории'),
        Column(
            Button(Const('Мужчины'), id='men_male_choose', on_click=getters.male_choose),
            Button(Const('Женщины'), id='women_male_choose', on_click=getters.male_choose),
            Button(Const('Любой'), id='any_male_choose', on_click=getters.male_choose),
        ),
        SwitchTo(Const('Назад'), id='back_get_volume', state=startSG.get_volume),
        state=startSG.get_male
    ),
    Window(
        Const('Укажите дату начала'),
        Calendar(id='get_date', on_click=getters.get_date), # возможно надо будет добавить кнопку сегодняшней даты
        SwitchTo(Const('🔙Назад'), id='back_get_male', state=startSG.get_male),
        state=startSG.get_date
    ),
    Window(
        Const('Выберите время начала'),
        Row(
            Button(Const('10:00'), id='morning_time_choose', on_click=getters.time_choose),
            Button(Const('18:00'), id='evening_time_choose', on_click=getters.time_choose),
        ),
        SwitchTo(Const('🔙Назад'), id='back_get_date', state=startSG.get_date),
        state=startSG.get_time
    ),
    Window(
        Format('На канал с ссылкой {channel} {date} в {time} начнется накрутка аудитории в кол-ве '
               '{volume} человек ({male}), верно?'),
        Row(
            Button(Const('Да'), id='add_task', on_click=getters.add_task),
            SwitchTo(Const('Изменить'), id='input_again_switcher', state=startSG.get_channel),
        ),
        SwitchTo(Const('🔙Назад'), id='back_get_time', state=startSG.get_time),
        getter=getters.confirm_task_getter,
        state=startSG.confirm_task
    ),
)