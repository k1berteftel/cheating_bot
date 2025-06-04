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
            SwitchTo(Const('Начать накрутку'), id='get_channel_switcher', state=startSG.get_channel),
            #SwitchTo(Const('Отложенные задачи'), id='deferred_tasks_menu', state=startSG.deferred_tasks_menu),
        ),
        state=startSG.start
    ),
    #Window(Const()),
    Window(
        Const('Введите ссылку на канал'),
        TextInput(
            id='get_channel',
            on_success=getters.get_channel
        ),
        SwitchTo(Const('Назад'), id='back', state=startSG.start),
        state=startSG.get_channel
    ),
    Window(
        Const('Введите общее кол-во человек для накрутки'),
        TextInput(
            id='get_volume',
            on_success=getters.get_volume # не меньше 10
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