import datetime
from mtag.helper import datetime_helper


def to_timeline_x(x_position: float, canvas_width: int, canvas_side_padding: float):
    max_timeline_x = canvas_width - canvas_side_padding
    min_timeline_x = canvas_side_padding

    timeline_x = max(x_position, min_timeline_x)
    timeline_x = min(max_timeline_x, timeline_x)
    return timeline_x


def pixel_to_datetime(x_position: float, timeline_side_padding: float,
                      pixels_per_second: float, current_date: datetime.datetime,
                      timeline_start_datetime: datetime.datetime,
                      timeline_stop_datetime: datetime.datetime) -> datetime.datetime:
    total_seconds = (x_position - timeline_side_padding) / pixels_per_second
    hours, minutes, seconds = datetime_helper.seconds_to_hour_minute_second(total_seconds=int(total_seconds))
    actual_timedelta = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
    start_timedelta = datetime.timedelta(hours=timeline_start_datetime.hour,
                                         minutes=timeline_start_datetime.minute,
                                         seconds=timeline_start_datetime.second)
    actual_time = current_date + actual_timedelta + start_timedelta

    boundary_timedelta = datetime.timedelta(hours=timeline_stop_datetime.hour,
                                            minutes=timeline_stop_datetime.minute,
                                            seconds=timeline_stop_datetime.second)

    boundary_time = current_date + boundary_timedelta

    time_to_use = actual_time if actual_time < boundary_time else boundary_time
    return time_to_use


def datetime_to_pixel(dt: datetime.datetime, current_date: datetime.datetime,
                      pixels_per_second: float, timeline_side_padding: float,
                      timeline_start_dt: datetime.datetime,
                      timeline_stop_dt: datetime.datetime) -> float:
    hour, minute, second = dt.hour, dt.minute, dt.second
    if dt < timeline_start_dt:
        hour, minute, second = timeline_start_dt.hour, timeline_start_dt.minute, timeline_start_dt.second
    elif timeline_stop_dt <= dt:
        hour, minute, second = timeline_stop_dt.hour, timeline_stop_dt.minute, timeline_stop_dt.second

    current_time = current_date + datetime.timedelta(hours=hour, minutes=minute, seconds=second)
    timeline_start_as_delta = datetime.timedelta(hours=timeline_start_dt.hour,
                                                 minutes=timeline_start_dt.minute,
                                                 seconds=timeline_start_dt.second)

    time_to_use = current_time - timeline_start_as_delta

    total_seconds = (time_to_use.hour * 60 * 60 + time_to_use.minute * 60 + time_to_use.second)
    return pixels_per_second * total_seconds + timeline_side_padding
