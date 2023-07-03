import typing as _
import re
import time as _time
from functools import wraps
from datetime import datetime, date, time


class date_pattern:
    ONLY_DAY = re.compile(r'^(\d+)$')
    DAY_MONTH = re.compile(r'^(\d+)[\s\.\-\\](\d+)$')  # separator: . - \ <space>
    DAY_MONTH_YEAR = re.compile(r'^(\d+)[\s\.\-\\](\d+)[\s\.\-\\](\d+)$')


class time_pattern:
    ONLY_HOUR = re.compile(r'^(\d+)$')
    HOUR_MINUTE = re.compile(r'^(\d+)[\s\.\:\-](\d+)$')  # separator: . : - <space>
    HOUR_MINUTE_SECOND = re.compile(r'^(\d+)[\s\.\:\-](\d+)[\s\.\:\-](\d+)$')


def dateformat(value: str) -> str:
    if match := date_pattern.ONLY_DAY.match(value):
        day = match.group(1)
        today = datetime.today()
        value = date(today.year, today.month, int(day))
        return value.strftime('%d-%m-%Y')

    elif match := date_pattern.DAY_MONTH.match(value):
        day, month = match.groups()
        today = datetime.today()
        value = date(today.year, int(month), int(day))
        return value.strftime('%d-%m-%Y')

    elif match := date_pattern.DAY_MONTH_YEAR.match(value):
        day, month, year = match.groups()
        value = date(int(year), int(month), int(day))
        return value.strftime('%d-%m-%Y')
    else:
        print('UNMATCHED:', value)


def timeformat(value: str) -> str:
    if match := time_pattern.ONLY_HOUR.match(value):
        hour = match.group(1)
        value = time(int(hour), 0, 0)
        return value.strftime('%H:%M:%S')
    elif match := time_pattern.HOUR_MINUTE.match(value):
        hour, minute = match.groups()
        value = time(int(hour), int(minute), 0)
        return value.strftime('%H:%M:%S')
    elif match := time_pattern.HOUR_MINUTE_SECOND.match(value):
        hour, minute, second = match.groups()
        value = time(int(hour), int(minute), int(second))
        return value.strftime('%H:%M:%S')


def timeit(func: _.Callable) -> _.Callable:
    @wraps(func)
    def _timeit(*args, **kwargs) -> _.Any:
        start = _time.time_ns()
        result = func(*args, **kwargs)
        stop = _time.time_ns()

        print(f'{func.__name__}: {(stop-start)/1_000_000}')
        return result

    return _timeit
