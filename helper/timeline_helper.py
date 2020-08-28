import datetime
from helper import datetime_helper


def to_timeline_x(x_position: float, canvas_width: int, canvas_side_padding: int):
    max_timeline_x = canvas_width - canvas_side_padding
    min_timeline_x = canvas_side_padding

    timeline_x = max(x_position, min_timeline_x)
    timeline_x = min(max_timeline_x, timeline_x)
    return timeline_x


def pixel_to_datetime(x_position: float, timeline_side_padding: int,
                      pixels_per_second: float, current_date: datetime.datetime,
                      timeline_start_datetime: datetime.datetime,
                      timeline_stop_datetime: datetime.datetime) -> datetime.datetime:
    total_seconds = (x_position - timeline_side_padding) / pixels_per_second
    hours, minutes, seconds = datetime_helper.seconds_to_hour_minute_second(total_seconds=total_seconds)
    actual_time = datetime.time(hour=hours, minute=minutes, second=seconds)

    is_stop_on_same_day_as_current = timeline_stop_datetime.day == current_date.day
    if is_stop_on_same_day_as_current:
        boundary_time = datetime.time(hour=timeline_stop_datetime.hour,
                                      minute=timeline_stop_datetime.minute,
                                      second=timeline_stop_datetime.second)
    else:
        boundary_time = datetime.time(hour=23, minute=59, second=59)

    time_to_use = actual_time if actual_time < boundary_time else boundary_time

    d = datetime.datetime(year=current_date.year,
                          month=current_date.month,
                          day=current_date.day)
    d += datetime.timedelta(hours=time_to_use.hour, minutes=time_to_use.minute, seconds=time_to_use.second)
    return d


def datetime_to_pixel(dt: datetime.datetime, current_date: datetime.datetime,
                      pixels_per_second: float, timeline_side_padding: int,
                      timeline_start_datetime: datetime.datetime,
                      timeline_stop_datetime: datetime.datetime) -> float:
    hour, minute, second = dt.hour, dt.minute, dt.second
    if dt < current_date:
        hour, minute, second = 0, 0, 0
    elif timeline_stop_datetime <= dt:
        if timeline_stop_datetime.day != current_date.day:
            hour, minute, second = 23, 59, 59
        else:
            hour, minute, second = timeline_stop_datetime.hour, timeline_stop_datetime.minute, timeline_stop_datetime.second

    hour_to_use = hour - timeline_start_datetime.hour
    minute_to_use = minute - timeline_start_datetime.minute
    second_to_use = second - timeline_start_datetime.second

    return pixels_per_second * (hour_to_use * 60 * 60 + minute_to_use * 60 + second_to_use) + timeline_side_padding
