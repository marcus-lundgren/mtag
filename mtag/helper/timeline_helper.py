from datetime import datetime, timedelta
from typing import Tuple

from mtag.helper import datetime_helper


MIN_BOUNDARY = 30 * 60
MAX_BOUNDARY = 24 * 60 * 60 - 1
ZOOM_STEP_IN_MINUTES = 15
MOVE_STEP_IN_MINUTES = 8


def to_timeline_x(x_position: float, canvas_width: int, canvas_side_padding: float) -> float:
    max_timeline_x = canvas_width - canvas_side_padding
    min_timeline_x = canvas_side_padding

    timeline_x = max(x_position, min_timeline_x)
    timeline_x = min(max_timeline_x, timeline_x)
    return timeline_x


def zoom(mouse_datetime: datetime, boundary_start: datetime, boundary_stop: datetime,
         zoom_in: bool) -> Tuple[datetime, datetime]:
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


def move(boundary_start: datetime, boundary_stop: datetime, move_right: bool) -> Tuple[datetime, datetime]:
    new_start = boundary_start
    boundary_delta = boundary_stop - boundary_start
    current_date = boundary_start.replace(hour=0, minute=0, second=0, microsecond=0)

    if move_right:
        new_start += timedelta(minutes=MOVE_STEP_IN_MINUTES)
        if (new_start + boundary_delta).day != current_date.day:
            new_start = current_date.replace(hour=23, minute=59, second=59) - boundary_delta
    else:
        new_start -= timedelta(minutes=MOVE_STEP_IN_MINUTES)
        if new_start < current_date:
            new_start = current_date

    return new_start, new_start + boundary_delta


def pixel_to_datetime(x_position: float, timeline_side_padding: float, canvas_width: int,
                      timeline_start_datetime: datetime, timeline_stop_datetime: datetime) -> datetime:
    if x_position - timeline_side_padding <= 0:
        return timeline_start_datetime
    elif canvas_width - timeline_side_padding <= x_position:
        return timeline_stop_datetime

    canvas_width_minus_padding = canvas_width - (timeline_side_padding * 2)
    x_position_to_use = x_position - timeline_side_padding
    boundary_delta = timeline_stop_datetime - timeline_start_datetime
    relative_pixel_delta = x_position_to_use / canvas_width_minus_padding

    return relative_pixel_delta * boundary_delta + timeline_start_datetime


def datetime_to_pixel(dt: datetime, canvas_width: int, timeline_side_padding: float,
                      timeline_start_dt: datetime, timeline_stop_dt: datetime) -> float:
    if dt <= timeline_start_dt:
        return timeline_side_padding
    elif timeline_stop_dt <= dt:
        return canvas_width - timeline_side_padding

    canvas_width_minus_padding = canvas_width - (timeline_side_padding * 2)
    boundary_delta = timeline_stop_dt - timeline_start_dt
    delta_from_start = dt - timeline_start_dt

    relative_dt_delta = delta_from_start.total_seconds() / boundary_delta.total_seconds()
    return relative_dt_delta * canvas_width_minus_padding + timeline_side_padding
