import datetime

from mtag.helper import timeline_helper

import cairo
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GObject


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
        self.current_date = datetime.datetime.now().replace(hour=0,
                                                            minute=0,
                                                            second=0,
                                                            microsecond=0)
        self.end_of_current_date = self.current_date.replace(hour=23, minute=59, second=59)
        self.boundary_start = self.current_date.replace(hour=4, minute=15)
        self.boundary_stop = self.boundary_start.replace(hour=8)
        self.side_padding = 20
        self.button_is_pressed = False

        self.set_size_request(-1, 80)
        self.show_all()

    def set_boundaries(self, start: datetime.datetime, stop: datetime.datetime):
        self.current_date = start.replace(hour=0, minute=0, second=0, microsecond=0)
        self.end_of_current_date = self.current_date.replace(hour=23, minute=59, second=59)
        self.boundary_start = start
        self.boundary_stop = stop
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
        self.pixels_per_second = (width - self.side_padding * 2) / (23 * 60 * 60 + 59 * 60 + 60)

        current_dt = self.current_date
        cr.set_font_size(16)
        for h in range(24):
            hx = self._datetime_to_pixel(dt=current_dt)
            cr.set_source_rgb(0.3, 0.3, 0.3)

            hour_string = str(current_dt.hour).rjust(2, '0')
            (tx, _, hour_text_width, hour_text_height, dx, _) = cr.text_extents(hour_string)
            cr.move_to(hx - tx - (hour_text_width / 2), (height + hour_text_height) / 2)
            cr.show_text(hour_string)

            current_dt += datetime.timedelta(hours=1)

        start_x = self._datetime_to_pixel(dt=self.boundary_start)
        stop_x = self._datetime_to_pixel(dt=self.boundary_stop)

        cr.set_source_rgba(0.6, 0.6, 0.2, 0.5)
        cr.rectangle(start_x, 0, stop_x - start_x, height)
        cr.fill()

    def _pixel_to_datetime(self, x_position: float) -> datetime:
        timeline_x = timeline_helper.to_timeline_x(x_position=x_position,
                                                   canvas_width=self.get_allocated_width(),
                                                   canvas_side_padding=self.side_padding)
        return timeline_helper.pixel_to_datetime(x_position=timeline_x,
                                                 timeline_side_padding=self.side_padding,
                                                 pixels_per_second=self.pixels_per_second,
                                                 current_date=self.current_date,
                                                 timeline_start_datetime=self.current_date,
                                                 timeline_stop_datetime=self.end_of_current_date)

    def _datetime_to_pixel(self, dt: datetime.datetime):
        return timeline_helper.datetime_to_pixel(dt=dt,
                                                 current_date=self.current_date,
                                                 pixels_per_second=self.pixels_per_second,
                                                 timeline_side_padding=self.side_padding,
                                                 timeline_start_dt=self.current_date,
                                                 timeline_stop_dt=self.end_of_current_date)
