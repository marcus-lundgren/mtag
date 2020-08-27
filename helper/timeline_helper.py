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

    is_stop_on_same_day_as_current = timeline_stop_datetime.day == current_date.day
    max_hour = timeline_stop_datetime.hour if is_stop_on_same_day_as_current else 23

    hour_to_use = hours + timeline_start_datetime.hour
    hour_to_use = min(hour_to_use, max_hour)

    minute_to_use = minutes + timeline_start_datetime.minute
    second_to_use = seconds + timeline_start_datetime.second

    if hour_to_use == max_hour:
        max_minute = timeline_stop_datetime.minute if is_stop_on_same_day_as_current else 59
        minute_to_use = min(minute_to_use, max_minute)

        if minute_to_use == max_minute:
            max_second = timeline_stop_datetime.second if is_stop_on_same_day_as_current else 59
            second_to_use = min(second_to_use, max_second)

    d = datetime.datetime(year=current_date.year,
                          month=current_date.month,
                          day=current_date.day)
    d += datetime.timedelta(hours=hour_to_use, minutes=minute_to_use, seconds=second_to_use)
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
