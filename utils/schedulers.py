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


async def start_fill_process(account: str, user_id: int, channel: str, volume: int, male: str, date: datetime, bot: Bot, scheduler: AsyncIOScheduler):
    await bot.send_message(
        chat_id=user_id,
        text='Процесс накрутки был успешно запущен'
    )
    group = get_sub_groups(volume, 'morning' if date.hour == 10 else 'evening')
    print(group)
    cookies = account + '.json'
    print(cookies)
    await fill_queue(cookies, group, channel, male, date, scheduler)


async def fill_queue(cookies: str, group: list[int], channel: str, male: str, time: datetime, scheduler: AsyncIOScheduler):
    result = check_remains_sum(group)
    if type(result) == int:
        hours = len(group)
        group = []
        await add_fill_task(cookies, *format_data(channel, result, male, hours))
    elif group[0] < 10:
        old_len = len(group)
        group, volume = collect_fill_group(group)
        new_len = len(group)
        time += timedelta(hours=old_len - new_len)
        print('short fill: ', *format_data(channel, volume, male, old_len - new_len))
        await add_fill_task(cookies, *format_data(channel, volume, male, old_len - new_len))
    else:
        volume = group.pop(0)
        time += timedelta(hours=1)
        print('basic fill: ', *format_data(channel, volume, male))
        await add_fill_task(cookies, *format_data(channel, volume, male))
    if len(group) == 0:
        return
    scheduler.add_job(
        fill_queue,
        args=[cookies, group, channel, male, time, scheduler],
        next_run_time=time
    )




