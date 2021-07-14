from datetime import datetime, timedelta
from typing import Tuple

from mtag.helper import datetime_helper


class TimelineHelper:
    MIN_BOUNDARY = 5 * 60
    MAX_BOUNDARY = 24 * 60 * 60 - 1
    ZOOM_STEP_IN_PERCENT = 3
    MOVE_STEP_IN_PERCENT = 5

    def __init__(self, canvas_width: int, timeline_side_padding: float,
                 timeline_start_dt: datetime, timeline_stop_dt: datetime):
        self.canvas_width = canvas_width
        self.timeline_side_padding = timeline_side_padding
        self.start_dt = timeline_start_dt
        self.stop_dt = timeline_stop_dt
        self.boundary_delta_dt = self.stop_dt - self.start_dt
        self.boundary_delta_in_seconds = self.boundary_delta_dt.total_seconds()
        self.max_x_in_timeline = self.canvas_width - self.timeline_side_padding
        self.canvas_width_without_padding = self.canvas_width - (self.timeline_side_padding * 2)

    def to_timeline_x(self, x_position: float) -> float:
        timeline_x = max(x_position, self.timeline_side_padding)
        timeline_x = min(self.max_x_in_timeline, timeline_x)
        return timeline_x

    @staticmethod
    def zoom(mouse_datetime: datetime, boundary_start: datetime, boundary_stop: datetime,
             zoom_in: bool) -> Tuple[datetime, datetime]:
        boundary_delta = boundary_stop - boundary_start
        zoom_step = boundary_delta * TimelineHelper.ZOOM_STEP_IN_PERCENT / 100
        mouse_delta = mouse_datetime - boundary_start
        boundary_delta_in_seconds = boundary_delta.total_seconds()
        mouse_relative_position = mouse_delta.total_seconds() / boundary_delta_in_seconds
        current_date = boundary_start.replace(hour=0, minute=0, second=0, microsecond=0)

        new_boundary_start = boundary_start

        # Zoom in
        if zoom_in:
            if boundary_delta_in_seconds >= TimelineHelper.MIN_BOUNDARY:
                old_relative_mouse_pos_in_seconds = mouse_relative_position * boundary_delta_in_seconds
                boundary_delta -= zoom_step
                new_relative_mouse_pos_in_seconds = int(boundary_delta.total_seconds() * mouse_relative_position)

                seconds_to_add_to_start = old_relative_mouse_pos_in_seconds - new_relative_mouse_pos_in_seconds
                hour, minute, second = datetime_helper.seconds_to_hour_minute_second(seconds_to_add_to_start)
                delta_to_add = timedelta(hours=hour, minutes=minute, seconds=second)
                new_boundary_start += delta_to_add
        # Zoom out
        else:
            if boundary_delta_in_seconds < TimelineHelper.MAX_BOUNDARY:
                old_relative_mouse_pos_in_seconds = mouse_relative_position * boundary_delta_in_seconds
                boundary_delta += zoom_step

                # Ensure that we don't zoom out too much
                if TimelineHelper.MAX_BOUNDARY <= boundary_delta.total_seconds():
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

    @staticmethod
    def move(boundary_start: datetime, boundary_stop: datetime, move_right: bool) -> Tuple[datetime, datetime]:
        new_start = boundary_start
        boundary_delta = boundary_stop - boundary_start
        move_step = boundary_delta * TimelineHelper.MOVE_STEP_IN_PERCENT / 100
        current_date = boundary_start.replace(hour=0, minute=0, second=0, microsecond=0)

        if move_right:
            new_start += move_step
            if (new_start + boundary_delta).day != current_date.day:
                new_start = current_date.replace(hour=23, minute=59, second=59) - boundary_delta
        else:
            new_start -= move_step
            if new_start < current_date:
                new_start = current_date

        return new_start, new_start + boundary_delta

    def pixel_to_datetime(self, x_position: float) -> datetime:
        if x_position - self.timeline_side_padding <= 0:
            return self.start_dt
        elif self.max_x_in_timeline <= x_position:
            return self.stop_dt

        x_position_to_use = x_position - self.timeline_side_padding
        relative_pixel_delta = x_position_to_use / self.canvas_width_without_padding
        return relative_pixel_delta * self.boundary_delta_dt + self.start_dt

    def datetime_to_pixel(self, dt: datetime) -> float:
        delta_from_start = dt - self.start_dt
        relative_dt_delta = delta_from_start.total_seconds() / self.boundary_delta_in_seconds
        return relative_dt_delta * self.canvas_width_without_padding + self.timeline_side_padding
