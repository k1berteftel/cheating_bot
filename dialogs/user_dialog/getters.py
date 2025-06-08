import datetime

from aiogram import Bot
from aiogram.types import CallbackQuery, User, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import Button, Select, ManagedCalendar
from aiogram_dialog.widgets.input import ManagedTextInput
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.schedulers import start_fill_process
from utils.build_ids import get_random_id
from utils.request_funcs import get_cookies
from utils.errors import AuthError, CaptchaError
from database.action_data_class import DataInteraction
from database.model import AccountsTable
from config_data.config import load_config, Config
from states.state_groups import startSG


config: Config = load_config()


async def disable_task_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    scheduler: AsyncIOScheduler = dialog_manager.middleware_data.get("scheduler")
    account_id = dialog_manager.dialog_data.get('account_id')
    buttons = []
    jobs = scheduler.get_jobs()
    for job in jobs:
        if job.id.startswith(str(account_id)):
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
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    scheduler: AsyncIOScheduler = dialog_manager.middleware_data.get("scheduler")
    account_id = dialog_manager.dialog_data.get('account_id')
    text = ''
    jobs = scheduler.get_jobs()
    for job in jobs:
        if job.id.startswith(str(account_id)):
            args = job.args
            channel, volume, male, date = args[2], args[3], args[4], args[5]
            male = 'Мужская' if male == 'men' else 'Женская' if male == 'women' else 'Любая'
            text += f'ID({job.id.split('_')[-1]}) <a href="{channel}">Канал</a>🔗|{volume} пдп ({male})|Запуск {date.strftime('%d-%m-%Y %H:%M')}\n'
    return {'jobs': text if text else 'Отсутствуют'}


async def choose_account_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(event_from_user.id)
    accounts: list[AccountsTable] = user.accounts
    buttons = []
    for account in accounts:
        buttons.append((account.name, account.id))
    return {'items': buttons}


async def choose_account(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data['account_id'] = int(item_id)
    await dialog_manager.switch_to(startSG.cheating_menu)


async def del_account_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(event_from_user.id)
    accounts: list[AccountsTable] = user.accounts
    buttons = []
    for account in accounts:
        buttons.append((account.name, account.id))
    return {'items': buttons}


async def choose_account_del(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    await session.del_account(int(item_id))
    await dialog_manager.switch_to(startSG.start)


async def start_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(event_from_user.id)
    accounts = False
    if user.accounts:
        accounts = True
    return {'accounts': accounts}


async def get_login(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    dialog_manager.dialog_data['login'] = text
    await dialog_manager.switch_to(startSG.get_password)


async def get_password(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    dialog_manager.dialog_data['password'] = text
    await dialog_manager.switch_to(startSG.get_account_name)


async def get_account_name(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    login = dialog_manager.dialog_data.get('login')
    password = dialog_manager.dialog_data.get('password')
    message = await msg.answer('Запущен процесс попытки входа, ожидайте')
    try:
        cookies = await get_cookies(login, password)
    except CaptchaError:
        await message.delete()
        await msg.answer('Проблемы с прохождением каптчи, пожалуйста попробуйте чуть позже')
        dialog_manager.dialog_data.clear()
        await dialog_manager.switch_to(startSG.start)
        return
    except AuthError:
        await message.delete()
        await msg.answer('Неверно указанны логин или пароль, пожалуйста попробуйте eще раз')
        dialog_manager.dialog_data.clear()
        await dialog_manager.switch_to(startSG.get_login)
        return
    await message.delete()
    await session.add_account(msg.from_user.id, text, login, password, cookies)
    dialog_manager.dialog_data.clear()
    await msg.answer('✅Аккаунт был успешно добавлен')
    await dialog_manager.switch_to(startSG.start)


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
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    account_id = dialog_manager.dialog_data.get('account_id')
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
    job_id = f'{account_id}_{get_random_id()}'
    scheduler.add_job(
        start_fill_process,
        args=[account_id, clb.from_user.id, channel, volume, male, date, bot, session, scheduler],
        next_run_time=date,
        id=job_id
    )
    await clb.message.answer('Задача накрутки была успешно добавлена')
    dialog_manager.dialog_data.clear()
    dialog_manager.dialog_data['account_id'] = account_id
    await dialog_manager.switch_to(startSG.cheating_menu)
