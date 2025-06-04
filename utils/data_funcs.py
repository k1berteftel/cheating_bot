import math
from typing import Literal

morning = [29, 15, 9, 5, 5, 3, 3, 3, 4, 3, 2, 2, 1, 1, 1, 0.5, 0.25, 0.5, 1, 1, 2, 3, 4, 2]

evening = [28, 14, 8, 6, 4, 3, 2, 1, 0.5, 0.5, 0.5, 0.5, 3, 5, 5, 4, 4, 2, 2, 3, 2, 1, 1, 1]


def get_sub_groups(volume: int, mode: Literal['morning', 'evening']) -> list[int]:
    percents = morning if mode == 'morning' else evening
    groups = []
    for percent in percents:
        groups.append(int(round(volume * percent / 100)))
    return groups


def collect_fill_group(group: list[int]):
    sum = 0
    del_indexes = []
    print('group before ', group)
    for i in range(0, len(group)):
        if group[i] < 10:
            print('add index: ', i, 'value: ', group[i])
            sum += group[i]
            del_indexes.append(i)
        else:
            print('end collect function, element: ', i, group[i])
            if sum >= 10:
                break
    print('indexes to del: ', del_indexes)
    del group[del_indexes[0]: del_indexes[-1] + 1]
    return group, sum


def format_data(channel: str, volume: int, male: str, hours: int = 1) -> tuple:
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

    return channel, volume, males[male], speed, sub_speed


def _get_allow_speed(volume: int) -> Literal[0, 1, 2, 3, 4]:
    allow_speeds = [30, 60, 180, 300, 600]
    speed = 0
    acceptable = abs(volume - allow_speeds[0])
    for i in range(1, len(allow_speeds)):
        differ = abs(volume - allow_speeds[i])
        if acceptable > differ:
            acceptable = differ
            speed = i
    return speed


def _get_custom_speed(volume: int, count: int) -> int:
    return math.ceil(count * 60 / volume)





