import datetime
import math
import random
from typing import Literal
from utils.request_funcs import Order


morning = [29, 14, 9, 6, 5, 4, 2.5, 3, 4, 3, 3, 2, 1.5, 1, 0.75, 0.5, 0.25, 0.5, 1, 1, 1.5, 2.5, 3, 2]

evening = [28, 14, 8, 6, 5, 3, 2.5, 2, 1, 0.5, 0.75, 1, 1.75, 2, 3, 2, 2.5, 2, 3.5, 2.5, 2, 2.5, 3, 2]


def get_sub_groups(volume: int, mode: Literal['morning', 'evening']) -> list[int]:
    percents = morning if mode == 'morning' else evening
    groups = []
    for percent in percents:
        groups.append(int(round(volume * percent / 100)))
    return groups


def collect_fill_group(group: list[int]):
    sum = 0
    del_indexes = []
    for i in range(0, len(group)):
        if sum < 10 or (len(group[i::]) == 1 and group[i] < 10):
            sum += group[i]
            del_indexes.append(i)
        else:
            if sum >= 10:
                break
    del group[del_indexes[0]: del_indexes[-1] + 1]
    return group, sum


def format_data(channel: str, volume: int, male: str, date: datetime.datetime, hours: int = 1) -> tuple:
    males = {
        'any': 0,
        'women': 1,
        'men': 2
    }
    sub_speed = None
    if hours == 1:
        speed = _get_allow_speed(volume)
    else:
        speed = 5
        sub_speed = _get_custom_speed(volume, hours)

    return channel, volume, males[male], date, speed, sub_speed


def _get_allow_speed(volume: int) -> int:
    allow_speeds = [30, 60, 180, 300, 600]
    speed = 0
    acceptable = abs(volume - allow_speeds[0])
    for i in range(1, len(allow_speeds)):
        differ = abs(volume - allow_speeds[i])
        if acceptable > differ:
            acceptable = differ
            speed = i
    return speed + 1 if allow_speeds[-1] != allow_speeds[speed] else speed


def _get_custom_speed(volume: int, count: int) -> int:
    return math.ceil(count * 60 / volume)


def check_remains_sum(group: list[int]) -> bool | int:
    remain = sum(group[1::])
    if remain >= 10 or len(group) == 1:
        return True
    volume = group[0] + remain
    return volume


def _append_fill(jobs_group: list[Order], fills: list[list[Order]]) -> list[list[Order]]:
    if fills and jobs_group[0].id in [job[0].id for job in fills]:
        for n in range(0, len(fills)):
            if jobs_group[0].id == fills[n][0].id:
                if len(jobs_group) > len(fills[n]):
                    fills[n] = jobs_group
                    break
    else:
        fills.append(jobs_group)
    return fills


def sort_orders(jobs: list[Order]) -> list[list[Order]]:
    fills = []
    jobs.sort(key=lambda x: x.create)
    for i in range(0, len(jobs)):
        jobs_group = [jobs[i]]
        for j in range(i+1, len(jobs)):
            differ = (jobs[i].create - jobs[j].create).total_seconds() / 60
            if jobs[i].start and 0 <= abs(differ) < 15 and jobs[j].start:
                jobs_group.append(jobs[j])
            else:
                break

        if len(jobs_group) != 1:
            if jobs_group[0].create < (datetime.datetime.today() - datetime.timedelta(days=3)):
                continue
            jobs_group.sort(key=lambda x: x.start)
            print('jobs_group: ', jobs_group)
            time_1 = jobs_group[0].start
            time_2 = jobs_group[-1].start
            period = int(abs((time_1 - time_2).total_seconds() / 3600))
            print(time_1, time_2, int(abs((time_1 - time_2).total_seconds() / 3600)), len(jobs_group))
            if period == 23 and len(jobs_group) >= 8:
                fills = _append_fill(jobs_group, fills)
            else:
                print('join else')
                if abs(period - 23) in range(0, 5) and len(jobs_group) >= 8:
                    job = jobs_group[-1]
                    if job.speed.startswith('задержка'):
                        delay = int(job.speed.split(' ')[1])
                        print('delay: ', delay)
                        if ((job.volume[1] // (60 / delay)) + period - 1) == 23:
                            fills = _append_fill(jobs_group, fills)
    return fills


def _test_fill():
    limits = [300, 400, 450, 500, 700]
    date = datetime.date.today()
    time = datetime.time(hour=18, minute=00)
    time = datetime.datetime.combine(date=date, time=time)
    for volume in limits:
        fill_imitation(volume, time)


def fill_imitation(count: int, time: datetime.datetime):
    import datetime
    speeds = {
        0: 'Очень медленная (30 пдп в час)',
        1: 'Медленная (60 пдп в час)',
        2: 'Средняя (180 пдп в час)',
        3: 'Быстрая (300 пдп в час)',
        4: 'Очень быстрая (600 пдп в час)'
    }
    print(f'Залив для {count} пдп')
    counter = 0
    group = get_sub_groups(count, 'evening')
    print(group[14::])

    for group in [group[0:4], group[14::]]:
        if counter == 1:
            time = time.replace(hour=8)
        print('fill imitation: ', group)
        while len(group) != 0:
            print('Время: ', time.strftime("%Y-%m-%d %H:%M:%S"))
            print(group)
            result = check_remains_sum(group)
            if type(result) == int:
                print('remains sum')
                hours = len(group)
                group = []
                data = format_data('', result, 'men', time, hours)
            elif group[0] < 10:
                old_len = len(group)
                group, volume = collect_fill_group(group)
                new_len = len(group)
                time += datetime.timedelta(hours=old_len - new_len)
                data = format_data('', volume, 'men', time, old_len - new_len)
            else:
                volume = group.pop(0)
                time += datetime.timedelta(hours=1)
                data = format_data('', volume, 'men', time)
            print('Кол-во пдп:', data[1], f'({round(data[1] / count * 100)} %)', '| Скорость залива:',
                  speeds[data[4]] if data[4] in range(0, 5) else f'1 пдп в {data[5]} минут')
        counter += 1
    print('\n\n')


#_test_fill()