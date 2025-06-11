import math
from typing import Literal

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
    count = 0
    del_indexes = []
    for i in range(0, len(group)):
        if group[i] < 10 and sum < 10:
            sum += group[i]
            del_indexes.append(i)
        else:
            if sum >= 10:
                break
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
    if remain > 10:
        return True
    volume = group[0] + remain
    return volume

