import datetime

from aiogram import Bot
from aiogram.types import CallbackQuery, User, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import Button, Select, ManagedCalendar
from aiogram_dialog.widgets.input import ManagedTextInput
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.schedulers import start_fill_process
from database.action_data_class import DataInteraction
from config_data.config import load_config, Config
from states.state_groups import startSG


config: Config = load_config()


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
    dialog_manager.dialog_data['date'] = date
    await dialog_manager.switch_to(startSG.get_time)


async def time_choose(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    time = clb.data.split('_')[0]
    if time == 'morning':
        time = datetime.time(hour=10, minute=00)
    else:
        time = datetime.time(hour=18, minute=00)
    dialog_manager.dialog_data['time'] = time
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
    bot: Bot = dialog_manager.middleware_data.get('bot')
    channel = dialog_manager.dialog_data.get('channel')
    volume = dialog_manager.dialog_data.get('volume')
    male = dialog_manager.dialog_data.get('male')
    date = dialog_manager.dialog_data.get('date')
    time = dialog_manager.dialog_data.get('time')
    date = datetime.datetime.combine(date=date, time=time)
    scheduler.add_job(
        start_fill_process,
        args=[clb.from_user.id, channel, volume, male, date, bot, scheduler],
        next_run_time=date
    )
    await clb.message.answer('Задача накрутки была успешно добавлена')
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(startSG.start)
