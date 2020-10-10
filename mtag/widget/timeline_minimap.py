import datetime

from mtag.helper import timeline_helper

import cairo
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk


class TimelineMinimap(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK
                        | Gdk.EventMask.BUTTON_PRESS_MASK
                        | Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.connect("draw", self._do_draw)
        self.current_date = datetime.datetime.now().replace(hour=0,
                                                            minute=0,
                                                            second=0,
                                                            microsecond=0)
        self.boundary_start = self.current_date.replace(hour=4, minute=15)
        self.boundary_stop = self.boundary_start.replace(hour=8)

        self.set_size_request(-1, 80)
        self.show_all()

    def set_boundaries(self, _, start: datetime.datetime, stop: datetime.datetime):
        self.current_date = start.replace(hour=0, minute=0, second=0, microsecond=0)
        self.boundary_start = start
        self.boundary_stop = stop
        self.queue_draw()

    def _do_draw(self, _: Gtk.DrawingArea, cr: cairo.Context):
        width = self.get_allocated_width()
        height = self.get_allocated_height()
        pixels_per_second = (width - 30) / (23 * 60 * 60 + 59 * 60 + 60)

        current_dt = self.current_date
        for h in range(24):
            hx = self._datetime_to_pixel(dt=current_dt, pixels_per_second=pixels_per_second)
            cr.set_source_rgb(0.3, 0.3, 0.3)
            cr.new_path()
            cr.move_to(hx, 0)
            cr.line_to(hx, height - 12)
            cr.stroke()

            hour_minute_string = f"{str(current_dt.hour).rjust(2, '0')}:00"
            (tx, _, hour_text_width, _, dx, _) = cr.text_extents(hour_minute_string)
            cr.move_to(hx - tx - (hour_text_width / 2), height)
            cr.show_text(hour_minute_string)

            current_dt += datetime.timedelta(hours=1)

        start_x = self._datetime_to_pixel(dt=self.boundary_start, pixels_per_second=pixels_per_second)
        stop_x = self._datetime_to_pixel(dt=self.boundary_stop, pixels_per_second=pixels_per_second)

        cr.set_source_rgba(0.6, 0.6, 0.2, 0.5)
        cr.rectangle(start_x, 0, stop_x - start_x, height)
        cr.fill()

    def _datetime_to_pixel(self, dt: datetime.datetime, pixels_per_second: float):
        return timeline_helper.datetime_to_pixel(dt=dt,
                                                 current_date=self.current_date,
                                                 pixels_per_second=pixels_per_second,
                                                 timeline_side_padding=15.0,
                                                 timeline_start_dt=self.current_date,
                                                 timeline_stop_dt=self.current_date.replace(hour=23,
                                                                                            minute=59,
                                                                                            second=59))
