import asyncio
from aiogram import Bot
from aiogram import Bot
from aiogram_dialog import DialogManager
from aiogram.types import InlineKeyboardMarkup, Message
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.action_data_class import DataInteraction

from utils.request_funcs import add_fill_task
from utils.data_funcs import get_sub_groups, collect_fill_group, format_data, check_remains_sum


async def sort_groups(channel: str, cookies: str, group: list[int], male_d: str, date: datetime) -> tuple[list[int], datetime]:
    new_group = group[:12:] if date.hour == 10 else group[0:4]
    await fill_queue(cookies, new_group, channel, male_d, date)
    males = {
        'any': 0,
        'women': 1,
        'men': 2
    }
    male = males[male_d]
    if 300 <= sum(group) < 650:
        await add_fill_task(cookies, channel, 12, male, date.replace(hour=22), 5, 8)
        await add_fill_task(cookies, channel, 10, male, date.replace(hour=0) + timedelta(days=1), 5, 21)
        await add_fill_task(cookies, channel, 10, male, date.replace(hour=4, minute=20) + timedelta(days=1), 5, 10)
        await add_fill_task(cookies, channel, 20, male, date.replace(hour=6, minute=25) + timedelta(days=1), 5, 5)
    elif 650 <= sum(group) <= 1000:
        await add_fill_task(cookies, channel, 20, male, date.replace(hour=22), 5, 6)
        await add_fill_task(cookies, channel, 10, male, date.replace(hour=0) + timedelta(days=1), 5, 10)
        await add_fill_task(cookies, channel, 10, male, date.replace(hour=2, minute=29) + timedelta(days=1), 5, 15)
        await add_fill_task(cookies, channel, 11, male, date.replace(hour=5) + timedelta(days=1), 0)
        await add_fill_task(cookies, channel, 13, male, date.replace(hour=6) + timedelta(days=1), 0)
        await add_fill_task(cookies, channel, 20, male, date.replace(hour=7) + timedelta(days=1), 0)
    elif 1000 < sum(group) <= 1300:
        await add_fill_task(cookies, channel, 18, male, date.replace(hour=22), 0)
        await add_fill_task(cookies, channel, 12, male, date.replace(hour=23), 0)
        await add_fill_task(cookies, channel, 14, male, date.replace(hour=0) + timedelta(days=1), 5, 7)
        await add_fill_task(cookies, channel, 10, male, date.replace(hour=2, minute=19) + timedelta(days=1), 5, 10)
        await add_fill_task(cookies, channel, 24, male, date.replace(hour=4, minute=30) + timedelta(days=1), 5, 3)
        await add_fill_task(cookies, channel, 45, male, date.replace(hour=6, minute=30) + timedelta(days=1), 5, 4)
    elif 1300 < sum(group) <= 1600:
        await add_fill_task(cookies, channel, 20, male, date.replace(hour=22), 0)
        await add_fill_task(cookies, channel, 15, male, date.replace(hour=23), 0)
        await add_fill_task(cookies, channel, 10, male, date.replace(hour=0) + timedelta(days=1), 5, 6)
        await add_fill_task(cookies, channel, 10, male, date.replace(hour=1) + timedelta(days=1), 5, 7)
        await add_fill_task(cookies, channel, 10, male, date.replace(hour=3) + timedelta(days=1), 5, 12)
        await add_fill_task(cookies, channel, 30, male, date.replace(hour=5, minute=35) + timedelta(days=1), 5, 2)
        await add_fill_task(cookies, channel, 30, male, date.replace(hour=7) + timedelta(days=1), 0)
    new_date = date.replace(hour=8) + timedelta(days=1)
    group = group[-2::] if date.hour == 10 else group[14::]
    return group, new_date


async def start_fill_process(account: str, user_id: int, channel: str, volume: int, male: str, date: datetime, bot: Bot):
    await bot.send_message(
        chat_id=user_id,
        text='Процесс накрутки был успешно запущен'
    )
    group = get_sub_groups(volume, 'morning' if date.hour == 10 else 'evening')
    print(group)
    cookies = account + '.json'
    print(cookies)
    if 300 <= sum(group) <= 1600:
        group, date = await sort_groups(channel, cookies, group, male, date)
    await fill_queue(cookies, group, channel, male, date)


async def fill_queue(cookies: str, group: list[int], channel: str, male: str, time: datetime):
    result = check_remains_sum(group)
    if type(result) == int:
        hours = len(group)
        group = []
        await add_fill_task(cookies, *format_data(channel, result, male, time, hours))
    elif group[0] < 10:
        old_len = len(group)
        group, volume = collect_fill_group(group)
        new_len = len(group)
        print('short fill: ', *format_data(channel, volume, male, time, old_len - new_len))
        await add_fill_task(cookies, *format_data(channel, volume, male, time, old_len - new_len))
        time += timedelta(hours=old_len - new_len)
    else:
        volume = group.pop(0)
        print('basic fill: ', *format_data(channel, volume, male, time))
        await add_fill_task(cookies, *format_data(channel, volume, male, time))
        time += timedelta(hours=1)
    if len(group) == 0:
        return
    await fill_queue(cookies, group, channel, male, time)

