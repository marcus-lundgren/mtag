import datetime
from helper import datetime_helper


def to_timeline_x(x_position: float, canvas_width: int, canvas_side_padding: int):
    max_timeline_x = canvas_width - canvas_side_padding - 0.00001
    min_timeline_x = canvas_side_padding

    timeline_x = max(x_position, min_timeline_x)
    timeline_x = min(max_timeline_x, timeline_x)
    return timeline_x


def pixel_to_datetime(x_position: float, timeline_side_padding: int,
                      pixels_per_second: float, current_date: datetime.datetime) -> datetime.datetime:
    total_seconds = (x_position - timeline_side_padding) / pixels_per_second
    hours, minutes, seconds = datetime_helper.seconds_to_hour_minute_second(total_seconds=total_seconds)
    d = datetime.datetime(year=current_date.year,
                          month=current_date.month,
                          day=current_date.day)
    d += datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
    return d


def datetime_to_pixel(dt: datetime.datetime, current_date: datetime.datetime,
                      pixels_per_second: float, timeline_side_padding: int) -> float:
    hour, minute, second = dt.hour, dt.minute, dt.second
    if dt < current_date:
        hour, minute, second = 0, 0, 0
    elif current_date + datetime.timedelta(days=1) <= dt:
        hour, minute, second = 23, 59, 59

    return pixels_per_second * (hour * 60 * 60 + minute * 60 + second) + timeline_side_padding
