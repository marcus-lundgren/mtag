import datetime


def is_within(to_check: datetime.datetime, start: datetime.datetime, stop: datetime.datetime):
    pass


def _to_two_digit(number: int):
    return str(number).rjust(2, "0")


def to_time_str(dt: datetime.datetime):
    return dt.strftime('%H:%M:%S')
