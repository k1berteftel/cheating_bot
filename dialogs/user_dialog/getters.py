import datetime

from aiogram import Bot
from aiogram.types import CallbackQuery, User, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import Button, Select, ManagedCalendar
from aiogram_dialog.widgets.input import ManagedTextInput
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.request_funcs import get_account_balance
from utils.schedulers import start_fill_process
from utils.build_ids import get_random_id
from database.model import AccountsTable
from config_data.config import load_config, Config
from states.state_groups import startSG

accounts = ['Основа', 'Запасной', 'Резервный', 'Дополнительный']

config: Config = load_config()


async def disable_task_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    scheduler: AsyncIOScheduler = dialog_manager.middleware_data.get("scheduler")
    account = dialog_manager.dialog_data.get('account')
    buttons = []
    jobs = scheduler.get_jobs()
    for job in jobs:
        if job.id.startswith(account):
            volume = job.args[3]
            buttons.append((f'{job.id.split("_")[-1]}({volume} пдп)', job.id))
    return {'items': buttons}


async def choose_job_del(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    scheduler: AsyncIOScheduler = dialog_manager.middleware_data.get("scheduler")
    job = scheduler.get_job(job_id=item_id)
    if job:
        job.remove()
    await dialog_manager.switch_to(startSG.disable_task)


async def tasks_menu_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    scheduler: AsyncIOScheduler = dialog_manager.middleware_data.get("scheduler")
    account = dialog_manager.dialog_data.get('account')
    text = ''
    jobs = scheduler.get_jobs()
    for job in jobs:
        if job.id.startswith(account):
            args = job.args
            channel, volume, male, date = args[2], args[3], args[4], args[5]
            male = 'Мужская' if male == 'men' else 'Женская' if male == 'women' else 'Любая'
            text += f'ID({job.id.split("_")[-1]}) <a href="{channel}">Канал</a>🔗|{volume} пдп ({male})|Запуск {date.strftime("%d-%m-%Y %H:%M")}\n'
    return {'jobs': text if text else 'Отсутствуют'}


async def choose_account_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    user_id = event_from_user.id
    if user_id == 5462623909 or user_id == 1236300146:
        accounts_list = accounts
    elif user_id == 2067909516:
        accounts_list = [accounts[-1]]
    elif user_id == 595650100:
        accounts_list = [accounts[1]]
    else:
        accounts_list = []
    buttons = []
    for index, account in enumerate(accounts_list):
        buttons.append((account, index))
    return {'items': buttons}


async def choose_account(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data['account'] = accounts[int(item_id)]
    await dialog_manager.switch_to(startSG.cheating_menu)


async def cheating_menu_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    account = dialog_manager.dialog_data.get('account')
    balance = await get_account_balance(account + '.json')
    return {'balance': str(balance) + ' Р' if balance else '<em>Ошибка при сборе ин-фо</em>'}


async def get_channel(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    if not text.startswith('https'):
        await msg.delete()
        await msg.answer('Ссылка на телеграмм канал должна начинаться с "https", пожалуйста попробуйте снова')
        return
    dialog_manager.dialog_data['channel'] = text
    await dialog_manager.switch_to(startSG.get_volume)


async def get_volume(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        volume = int(text)
    except Exception:
        await msg.delete()
        await msg.answer('Кол-во человек должно быть числом, пожалуйста попробуйте снова')
        return
    if volume < 10:
        await msg.delete()
        await msg.answer('Кол-во человек должно быть больше 10, пожалуйста введите новое значение')
        return
    dialog_manager.dialog_data['volume'] = volume
    await dialog_manager.switch_to(startSG.get_male)


async def male_choose(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    male = clb.data.split('_')[0]
    dialog_manager.dialog_data['male'] = male
    await dialog_manager.switch_to(startSG.get_date)


async def get_date(clb: CallbackQuery, widget: ManagedCalendar, dialog_manager: DialogManager, date: datetime.date):
    dialog_manager.dialog_data['date'] = date.isoformat()
    await dialog_manager.switch_to(startSG.get_time)


async def time_choose(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    time = clb.data.split('_')[0]
    if time == 'morning':
        time = datetime.time(hour=10, minute=00)
    else:
        time = datetime.time(hour=18, minute=00)
    dialog_manager.dialog_data['time'] = time.isoformat()
    await dialog_manager.switch_to(startSG.confirm_task)


async def confirm_task_getter(dialog_manager: DialogManager, **kwargs):
    channel = dialog_manager.dialog_data.get('channel')
    volume = dialog_manager.dialog_data.get('volume')
    male = dialog_manager.dialog_data.get('male')
    date = dialog_manager.dialog_data.get('date')
    time = dialog_manager.dialog_data.get('time')
    return {
        'channel': channel,
        'date': str(date),
        'time': str(time),
        'volume': volume,
        'male': 'Мужская' if male == 'men' else 'Женская' if male == 'women' else 'Любая'
    }


async def add_task(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    scheduler: AsyncIOScheduler = dialog_manager.middleware_data.get("scheduler")
    account = dialog_manager.dialog_data.get('account')
    bot: Bot = dialog_manager.middleware_data.get('bot')
    channel = dialog_manager.dialog_data.get('channel')
    volume = dialog_manager.dialog_data.get('volume')
    male = dialog_manager.dialog_data.get('male')

    date = dialog_manager.dialog_data.get('date')
    date = datetime.date.fromisoformat(date)

    time = dialog_manager.dialog_data.get('time')
    h, m, s = map(int, time.split(":"))
    time = datetime.time(h, m, s)

    date = datetime.datetime.combine(date=date, time=time)
    job_id = f'{account}_{get_random_id()}'
    scheduler.add_job(
        start_fill_process,
        args=[account, clb.from_user.id, channel, volume, male, date, bot, scheduler],
        next_run_time=date,
        id=job_id
    )
    await clb.message.answer('Задача накрутки была успешно добавлена')
    dialog_manager.dialog_data.clear()
    dialog_manager.dialog_data['account'] = account
    await dialog_manager.switch_to(startSG.cheating_menu)
