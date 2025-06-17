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


async def sort_groups(channel: str, cookies: str, group: list[int], male_d: str, scheduler: AsyncIOScheduler, date: datetime) -> list[int]:
    males = {
        'any': 0,
        'women': 1,
        'men': 2
    }
    male = males[male_d]
    if 300 <= sum(group) < 650:
        scheduler.add_job(
            add_fill_task,
            'interval',
            args=[cookies, channel, 12, male, 5, 8],
            next_run_time=date.replace(hour=22)
        )
        scheduler.add_job(
            add_fill_task,
            'interval',
            args=[cookies, channel, 10, male, 5, 21],
            next_run_time=date.replace(hour=0, day=date.day+1)
        )
        scheduler.add_job(
            add_fill_task,
            'interval',
            args=[cookies, channel, 10, male, 5, 10],
            next_run_time=date.replace(hour=4, minute=20, day=date.day+1)
        )
        scheduler.add_job(
            add_fill_task,
            'interval',
            args=[cookies, channel, 20, male, 5, 5],
            next_run_time=date.replace(hour=6, minute=25, day=date.day+1)
        )
    elif 650 <= sum(group) <= 1000:
        scheduler.add_job(
            add_fill_task,
            'interval',
            args=[cookies, channel, 20, male, 5, 6],
            next_run_time=date.replace(hour=22)
        )
        scheduler.add_job(
            add_fill_task,
            'interval',
            args=[cookies, channel, 10, male, 5, 10],
            next_run_time=date.replace(hour=0, day=date.day+1)
        )
        scheduler.add_job(
            add_fill_task,
            'interval',
            args=[cookies, channel, 10, male, 5, 15],
            next_run_time=date.replace(hour=2, minute=29, day=date.day+1)
        )
        scheduler.add_job(
            add_fill_task,
            'interval',
            args=[cookies, channel, 11, male, 0],
            next_run_time=date.replace(hour=5, day=date.day+1)
        )
        scheduler.add_job(
            add_fill_task,
            'interval',
            args=[cookies, channel, 13, male, 0],
            next_run_time=date.replace(hour=6, day=date.day+1)
        )
        scheduler.add_job(
            add_fill_task,
            'interval',
            args=[cookies, channel, 20, male, 0],
            next_run_time=date.replace(hour=7, day=date.day+1)
        )
    elif 1000 < sum(group) <= 1300:
        scheduler.add_job(
            add_fill_task,
            'interval',
            args=[cookies, channel, 18, male, 0],
            next_run_time=date.replace(hour=22)
        )
        scheduler.add_job(
            add_fill_task,
            'interval',
            args=[cookies, channel, 12, male, 0],
            next_run_time=date.replace(hour=23)
        )
        scheduler.add_job(
            add_fill_task,
            'interval',
            args=[cookies, channel, 14, male, 5, 7],
            next_run_time=date.replace(hour=0, day=date.day+1)
        )
        scheduler.add_job(
            add_fill_task,
            'interval',
            args=[cookies, channel, 10, male, 5, 10],
            next_run_time=date.replace(hour=2, minute=19, day=date.day+1)
        )
        scheduler.add_job(
            add_fill_task,
            'interval',
            args=[cookies, channel, 24, male, 5, 3],
            next_run_time=date.replace(hour=4, minute=30, day=date.day+1)
        )
        scheduler.add_job(
            add_fill_task,
            'interval',
            args=[cookies, channel, 45, male, 5, 4],
            next_run_time=date.replace(hour=6, minute=30, day=date.day+1)
        )
    new_date = date.replace(hour=8, day=date.day + 1)
    new_group = group[-2::] if date.hour == 10 else group[14::]
    print('c 8 до остатка ', new_group)
    scheduler.add_job(
        fill_queue,
        args=[cookies, new_group, channel, male_d, new_date, scheduler],
        next_run_time=new_date
    )
    group = group[:12:] if date.hour == 10 else group[0:4]
    return group


async def start_fill_process(account: str, user_id: int, channel: str, volume: int, male: str, date: datetime, bot: Bot, scheduler: AsyncIOScheduler):
    await bot.send_message(
        chat_id=user_id,
        text='Процесс накрутки был успешно запущен'
    )
    group = get_sub_groups(volume, 'morning' if date.hour == 10 else 'evening')
    print(group)
    cookies = account + '.json'
    print(cookies)
    if 300 <= sum(group) <= 1300:
        group = await sort_groups(channel, cookies, group, male, scheduler, date)
    print('до 22 ', group)
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




