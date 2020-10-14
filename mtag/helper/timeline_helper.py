from datetime import datetime, timedelta
from mtag.helper import datetime_helper


MIN_BOUNDARY = 30 * 60
MAX_BOUNDARY = 24 * 60 * 60 -1
ZOOM_STEP_IN_MINUTES = 15


def to_timeline_x(x_position: float, canvas_width: int, canvas_side_padding: float):
    max_timeline_x = canvas_width - canvas_side_padding
    min_timeline_x = canvas_side_padding

    timeline_x = max(x_position, min_timeline_x)
    timeline_x = min(max_timeline_x, timeline_x)
    return timeline_x


def zoom(mouse_datetime: datetime, boundary_start: datetime, boundary_stop: datetime, zoom_in: bool):
    boundary_delta = boundary_stop - boundary_start
    mouse_delta = mouse_datetime - boundary_start
    mouse_relative_position = mouse_delta.total_seconds() / boundary_delta.total_seconds()
    current_date = boundary_start.replace(hour=0, minute=0, second=0, microsecond=0)

    new_boundary_start = boundary_start

    # Zoom in
    if zoom_in:
        if boundary_delta.total_seconds() >= MIN_BOUNDARY:
            old_relative_mouse_pos_in_seconds = mouse_relative_position * boundary_delta.total_seconds()
            boundary_delta -= timedelta(minutes=ZOOM_STEP_IN_MINUTES)
            new_relative_mouse_pos_in_seconds = int(boundary_delta.total_seconds() * mouse_relative_position)

            seconds_to_add_to_start = old_relative_mouse_pos_in_seconds - new_relative_mouse_pos_in_seconds
            hour, minute, second = datetime_helper.seconds_to_hour_minute_second(seconds_to_add_to_start)
            delta_to_add = timedelta(hours=hour, minutes=minute, seconds=second)
            new_boundary_start += delta_to_add
    # Zoom out
    else:
        if boundary_delta.total_seconds() < MAX_BOUNDARY:
            old_relative_mouse_pos_in_seconds = mouse_relative_position * boundary_delta.total_seconds()
            boundary_delta += timedelta(minutes=ZOOM_STEP_IN_MINUTES)

            # Ensure that we don't zoom out too much
            if MAX_BOUNDARY <= boundary_delta.total_seconds():
                boundary_delta = timedelta(hours=23, minutes=59, seconds=59)
                new_boundary_start = current_date
            else:
                new_relative_mouse_pos_in_seconds = int(boundary_delta.total_seconds() * mouse_relative_position)
                seconds_to_add_to_start = old_relative_mouse_pos_in_seconds - new_relative_mouse_pos_in_seconds
                hour, minute, second = datetime_helper.seconds_to_hour_minute_second(seconds_to_add_to_start)
                delta_to_add = timedelta(hours=hour, minutes=minute, seconds=second)
                new_boundary_start += delta_to_add

            # Ensure that we don't get too far to the left
            if new_boundary_start < current_date:
                new_boundary_start = current_date

            # Ensure that we don't get too far to the right
            if (new_boundary_start + boundary_delta).day != current_date.day:
                new_boundary_start = current_date.replace(hour=23, minute=59, second=59) - boundary_delta

    return new_boundary_start, new_boundary_start + boundary_delta


def pixel_to_datetime(x_position: float, timeline_side_padding: float,
                      pixels_per_second: float, current_date: datetime,
                      timeline_start_datetime: datetime,
                      timeline_stop_datetime: datetime) -> datetime:
    total_seconds = (x_position - timeline_side_padding) / pixels_per_second
    hours, minutes, seconds = datetime_helper.seconds_to_hour_minute_second(total_seconds=int(total_seconds))
    actual_timedelta = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    start_timedelta = timedelta(hours=timeline_start_datetime.hour,
                                minutes=timeline_start_datetime.minute,
                                seconds=timeline_start_datetime.second)
    actual_time = current_date + actual_timedelta + start_timedelta

    boundary_timedelta = timedelta(hours=timeline_stop_datetime.hour,
                                   minutes=timeline_stop_datetime.minute,
                                   seconds=timeline_stop_datetime.second)

    boundary_time = current_date + boundary_timedelta

    time_to_use = actual_time if actual_time < boundary_time else boundary_time
    return time_to_use


def datetime_to_pixel(dt: datetime, current_date: datetime,
                      pixels_per_second: float, timeline_side_padding: float,
                      timeline_start_dt: datetime,
                      timeline_stop_dt: datetime) -> float:
    if dt < timeline_start_dt:
        hour, minute, second = timeline_start_dt.hour, timeline_start_dt.minute, timeline_start_dt.second
    elif timeline_stop_dt <= dt:
        hour, minute, second = timeline_stop_dt.hour, timeline_stop_dt.minute, timeline_stop_dt.second
    else:
        hour, minute, second = dt.hour, dt.minute, dt.second

    current_time = current_date.replace(hour=hour, minute=minute, second=second)
    timeline_start_as_delta = timedelta(hours=timeline_start_dt.hour,
                                        minutes=timeline_start_dt.minute,
                                        seconds=timeline_start_dt.second)

    time_to_use = current_time - timeline_start_as_delta

    total_seconds = (time_to_use.hour * 3600 + time_to_use.minute * 60 + time_to_use.second)
    return pixels_per_second * total_seconds + timeline_side_padding
