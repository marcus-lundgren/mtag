import datetime


def is_within(to_check: datetime.datetime, start: datetime.datetime, stop: datetime.datetime):
    pass


def _to_two_digit(number: int):
    return str(number).rjust(2, "0")


def to_time_str(dt: datetime.datetime):
    return dt.strftime('%H:%M:%S')


def to_duration_str(td: datetime.timedelta):
    hours, minutes, seconds = seconds_to_hour_minute_second(td.seconds)
    return f"{_to_two_digit(hours)}:{_to_two_digit(minutes)}:{_to_two_digit(seconds)}"


def seconds_to_hour_minute_second(total_seconds: int) -> tuple:
    hours = total_seconds // (60 * 60)
    minutes = (total_seconds - hours * 60 * 60) // 60
    seconds = int(total_seconds % 60)
    return int(hours), int(minutes), seconds

def to_time_text(start: datetime.datetime, stop: datetime.datetime, duration: datetime.timedelta):
    start_str = to_time_str(start)
    stop_str = to_time_str(stop)
    duration_str = to_duration_str(duration)
    return f"{start_str} - {stop_str} ({duration_str})"
