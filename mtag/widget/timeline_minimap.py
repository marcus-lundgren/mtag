import datetime
import math
from typing import List

import cairo
import gi

from mtag.helper import timeline_helper


gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GObject


class TimelineEntry:
    def __init__(self, start_x: float, stop_x: float):
        self.start_x = math.floor(start_x)
        self.width = math.ceil(stop_x) - self.start_x


class TimelineMinimap(Gtk.DrawingArea):
    @GObject.Signal(name="timeline-boundary-changed",
                    flags=GObject.SignalFlags.RUN_LAST,
                    return_type=GObject.TYPE_BOOLEAN,
                    arg_types=[object, object])
    def timeline_boundary_changed(self, *args):
        pass

    def __init__(self):
        super().__init__()
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK
                        | Gdk.EventMask.BUTTON_PRESS_MASK
                        | Gdk.EventMask.BUTTON_RELEASE_MASK
                        | Gdk.EventMask.SCROLL_MASK)
        self.connect("draw", self._do_draw)
        self.connect("button_press_event", self._do_button_press)
        self.connect("button_release_event", self._do_button_release)
        self.connect("motion_notify_event", self._do_motion_notify)
        self.connect("scroll_event", self._do_scroll_event)
        self.connect("configure-event", lambda *_: self._update_timeline_entries())
        self.current_date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.end_of_current_date = self.current_date.replace(hour=23, minute=59, second=59)
        self.boundary_start = self.current_date.replace(hour=4, minute=15)
        self.boundary_stop = self.boundary_start.replace(hour=8)
        self.side_padding = 20
        self.button_is_pressed = False
        self.logged_entries = []
        self.tagged_entries = []
        self.logged_timeline_entries: List[TimelineEntry] = []
        self.tagged_timeline_entries: List[TimelineEntry] = []

        self.set_size_request(-1, 80)
        self.show_all()

    def set_boundaries(self, start: datetime.datetime, stop: datetime.datetime):
        self.current_date = start.replace(hour=0, minute=0, second=0, microsecond=0)
        self.end_of_current_date = self.current_date.replace(hour=23, minute=59, second=59)
        self.boundary_start = start
        self.boundary_stop = stop
        self.queue_draw()

    def set_entries(self, current_date: datetime.datetime, logged_entries, tagged_entries) -> None:
        self.current_date = current_date
        self.end_of_current_date = self.current_date.replace(hour=23, minute=59, second=59)
        self.boundary_start = self.boundary_start.replace(year=current_date.year, month=current_date.month,
                                                          day=current_date.day)
        self.boundary_stop = self.boundary_stop.replace(year=current_date.year, month=current_date.month,
                                                        day=current_date.day)
        self.logged_entries = logged_entries
        self.tagged_entries = tagged_entries

        self._update_timeline_entries()
        self.queue_draw()

    def _set_boundaries_and_fire_new_boundary(self, actual_x: float):
        moused_dt = self._pixel_to_datetime(actual_x)
        current_delta = self.boundary_stop - self.boundary_start

        new_start = moused_dt - (current_delta / 2)
        # Ensure that we don't get too far to the left
        if new_start < self.current_date:
            new_start = self.current_date

        new_stop = new_start + current_delta
        # Ensure that we don't get too far to the right
        if self.end_of_current_date < new_stop:
            new_start -= new_stop - self.end_of_current_date
            new_stop = new_start + current_delta

        self.set_boundaries(start=new_start, stop=new_stop)
        self.emit("timeline-boundary-changed", self.boundary_start, self.boundary_stop)

    def _do_button_press(self, _, e: Gdk.EventButton):
        self.button_is_pressed = True
        self._set_boundaries_and_fire_new_boundary(actual_x=e.x)

    def _do_button_release(self, *_):
        self.button_is_pressed = False

    def _do_motion_notify(self, _, e: Gdk.EventMotion):
        if self.button_is_pressed:
            self._set_boundaries_and_fire_new_boundary(e.x)

    def _do_scroll_event(self, _, e: Gdk.EventScroll):
        mouse_datetime = self._pixel_to_datetime(e.x)

        # Zoom in or out
        if e.direction == Gdk.ScrollDirection.UP or e.direction == Gdk.ScrollDirection.DOWN:
            zoom_in = e.direction == Gdk.ScrollDirection.UP
            self.boundary_start, self.boundary_stop = timeline_helper.zoom(mouse_datetime=mouse_datetime,
                                                                           boundary_start=self.boundary_start,
                                                                           boundary_stop=self.boundary_stop,
                                                                           zoom_in=zoom_in)
        # Move right or left
        elif e.direction == Gdk.ScrollDirection.RIGHT or e.direction == Gdk.ScrollDirection.LEFT:
            move_right = e.direction == Gdk.ScrollDirection.RIGHT
            self.boundary_start, self.boundary_stop = timeline_helper.move(boundary_start=self.boundary_start,
                                                                           boundary_stop=self.boundary_stop,
                                                                           move_right=move_right)

        self.queue_draw()
        self.emit("timeline-boundary-changed", self.boundary_start, self.boundary_stop)

    def _do_draw(self, _: Gtk.DrawingArea, cr: cairo.Context):
        width = self.get_allocated_width()
        height = self.get_allocated_height()

        current_dt = self.current_date
        cr.set_font_size(16)
        cr.set_source_rgb(0.5, 0.5, 0.5)
        for h in range(24):
            hx = self._datetime_to_pixel(dt=current_dt, canvas_width=width)
            hour_string = str(current_dt.hour).rjust(2, '0')
            (tx, _, hour_text_width, hour_text_height, dx, _) = cr.text_extents(hour_string)
            cr.move_to(hx - tx - (hour_text_width / 2), (height + hour_text_height) / 2)
            cr.show_text(hour_string)

            current_dt += datetime.timedelta(hours=1)

        cr.set_source_rgb(1, 0.64, 0)
        for te in self.tagged_timeline_entries:
            cr.rectangle(te.start_x, 10, te.width, 20)
            cr.fill()

        cr.set_source_rgb(0.3, 0.3, 0.8)
        for le in self.logged_timeline_entries:
            cr.rectangle(le.start_x, 50, le.width, 20)
            cr.fill()

        start_x = self._datetime_to_pixel(dt=self.boundary_start, canvas_width=width)
        stop_x = self._datetime_to_pixel(dt=self.boundary_stop, canvas_width=width)

        cr.set_source_rgba(0.4, 0.4, 0.4, 0.5)
        cr.rectangle(start_x, 0, stop_x - start_x, height)
        cr.fill()

    def _pixel_to_datetime(self, x_position: float) -> datetime:
        return timeline_helper.pixel_to_datetime(x_position=x_position,
                                                 timeline_side_padding=self.side_padding,
                                                 canvas_width=self.get_allocated_width(),
                                                 timeline_start_datetime=self.current_date,
                                                 timeline_stop_datetime=self.end_of_current_date)

    def _datetime_to_pixel(self, dt: datetime.datetime, canvas_width: int):
        return timeline_helper.datetime_to_pixel(dt=dt,
                                                 canvas_width=canvas_width,
                                                 timeline_side_padding=self.side_padding,
                                                 timeline_start_dt=self.current_date,
                                                 timeline_stop_dt=self.end_of_current_date)

    def _update_timeline_entries(self):
        canvas_width = self.get_allocated_width()
        self.logged_timeline_entries = [TimelineEntry(self._datetime_to_pixel(le.start, canvas_width),
                                                      self._datetime_to_pixel(le.stop, canvas_width))
                                        for le in self.logged_entries]
        self.tagged_timeline_entries = [TimelineEntry(self._datetime_to_pixel(te.start, canvas_width),
                                                      self._datetime_to_pixel(te.stop, canvas_width))
                                        for te in self.tagged_entries]
