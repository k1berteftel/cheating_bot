import asyncio
import datetime

from aiogram import Bot
from aiogram.types import CallbackQuery, User, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import Button, Select, ManagedCalendar
from aiogram_dialog.widgets.input import ManagedTextInput
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.request_funcs import get_account_balance, get_account_jobs, Order, turn_off_job
from utils.data_funcs import sort_orders
from utils.schedulers import start_fill_process
from utils.build_ids import get_random_id
from database.model import AccountsTable
from config_data.config import load_config, Config
from states.state_groups import startSG

accounts = {
    'Алекс': 'Основа',
    'Артем': 'Запасной',
    'Алекс резерв.': 'Резервный',
    'Hugi': 'Дополнительный'
}

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


async def jobs_pager(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    if clb.data.startswith('next'):
        dialog_manager.dialog_data['page'] = dialog_manager.dialog_data.get('page') + 1
    else:
        dialog_manager.dialog_data['page'] = dialog_manager.dialog_data.get('page') - 1
    await dialog_manager.switch_to(startSG.tasks_menu)


async def tasks_menu_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    account = dialog_manager.dialog_data.get('account')
    buttons = dialog_manager.dialog_data.get("buttons")
    bot: Bot = dialog_manager.middleware_data.get('bot')
    print(buttons)
    if not buttons:
        buttons = []
        jobs = await get_account_jobs(account + '.json')
        print('jobs collect: ', jobs)
        jobs = sort_orders(jobs)
        print('after sort: ', jobs)
        if not jobs:
            await bot.send_message(
                chat_id=event_from_user.id,
                text='На этом аккаунте нету задач'
            )
            return {
                'items': [],
                'pages': '0/0'
            }
        dialog_manager.dialog_data['jobs'] = jobs
        for i in range(0, len(jobs)):
            buttons.append(
                (f'{jobs[i][0].start.strftime("%d-%m %H:%M")} - {jobs[i][-1].start.strftime("%H:%M")}', i)  #.strftime("%d-%m-%Y %H:%M")
            )
        buttons = [buttons[i:i + 20] for i in range(0, len(buttons), 20)]
        dialog_manager.dialog_data["buttons"] = buttons
    page = dialog_manager.dialog_data.get('page')
    if page is None:
        page = 0
        dialog_manager.dialog_data['page'] = page
    not_first = True
    not_last = True
    if page == 0:
        not_first = False
    if len(buttons) - 1 <= page:
        not_last = False
    return {
        'not_first': not_first,
        'not_last': not_last,
        'pages': f'{page}/{len(buttons)}',
        'items': buttons[page]
    }


async def job_selector(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    account = dialog_manager.dialog_data.get('account')
    jobs = dialog_manager.dialog_data.get('jobs')
    dialog_manager.dialog_data['job'] = jobs[int(item_id)]
    await dialog_manager.switch_to(startSG.job_menu)


async def job_menu_getter(dialog_manager: DialogManager, **kwargs):
    job: list[Order] = dialog_manager.dialog_data.get('job')
    text = (f'<b>Название канала:</b> {job[0].channel_name}\n'
            f'<b>Ссылка:</b> {job[0].link}\n<b>Пдп:</b> '
            f'{sum([task.volume[0] for task in job])}/{sum([task.volume[1] for task in job])}\n'
            f'<b>Пол:</b> {job[0].male}\n<b>Отложенный запуск:</b> {job[0].start.strftime("%d-%m-%Y %H:%M")}'
            f'\n<b>Создан:</b> {job[0].create.strftime("%d-%m-%Y %H:%M")}')
    return {'text': text}


async def disable_job(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    job: list[Order] = dialog_manager.dialog_data.get('job')
    account = dialog_manager.dialog_data.get('account')
    await clb.message.answer('Начался процесс удаления группы задач')
    result = await turn_off_job(account + '.json', job)
    if not result:
        await clb.answer('Произошла какая-то ошибка при удалении')
        await dialog_manager.switch_to(startSG.tasks_menu)
        return
    dialog_manager.dialog_data['jobs'] = None
    dialog_manager.dialog_data['job'] = None
    dialog_manager.dialog_data['page'] = None
    await clb.answer('Задача была успешно снята')
    await dialog_manager.switch_to(startSG.tasks_menu)


async def choose_account_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    user_id = event_from_user.id
    if user_id == 5462623909 or user_id == 1236300146:
        accounts_list = accounts
    elif user_id == 2067909516:
        accounts_list = dict([list(accounts.items())[-1]])
    elif user_id == 595650100:
        accounts_list = dict([list(accounts.items())[1]])
    else:
        accounts_list = {}
    buttons = []
    for name, account in accounts_list.items():
        buttons.append((name, name))
    return {'items': buttons}


async def choose_account(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data.clear()
    dialog_manager.dialog_data['account'] = accounts[item_id]
    await dialog_manager.switch_to(startSG.cheating_menu)


async def cheating_menu_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    account = dialog_manager.dialog_data.get('account')
    balance = await get_account_balance(account + '.json')
    return {'balance': str(balance) + ' Р' if balance is not None else '<em>Ошибка при сборе ин-фо</em>'}


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
    try:
        await start_fill_process(account, clb.from_user.id, channel, volume, male, date, bot),
    except Exception as err:
        print(err)
        await clb.message.answer('Во время постановки задачи произошла какая-то ошибка, пожалуйста попробуйте снова')

    await clb.message.answer('Задача накрутки была успешно добавлена')
    dialog_manager.dialog_data.clear()
    dialog_manager.dialog_data['account'] = account
    await dialog_manager.switch_to(startSG.cheating_menu, show_mode=ShowMode.DELETE_AND_SEND)
