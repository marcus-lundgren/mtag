import datetime

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk


class TimelineDetailsPopover(Gtk.Popover):
    def __init__(self, widget: Gtk.Widget):
        super().__init__()
        self.set_relative_to(widget)
        self.set_modal(False)
        self.set_position(Gtk.PositionType.BOTTOM)

        self.text_box = Gtk.TextView()
        self.text_box.set_cursor_visible(False)
        self.text_box.set_editable(False)
        self.add(self.text_box)
        self.show_all()
        self.hide()

        self.pointing_to_rectangle = Gdk.Rectangle()
        self.pointing_to_rectangle.x = 1
        self.pointing_to_rectangle.y = 1
        self.pointing_to_rectangle.width = 1
        self.pointing_to_rectangle.height = 1

        self.connect("enter-notify-event", self._on_enter)
        self.connect("leave-notify-event", self._on_leave)
        self.connect("motion-notify-event", self._on_motion)

    def _on_enter(self, w, e):
        return True

    def _on_leave(self, w, e):
        return True

    def _on_motion(self, w, e):
        return True

    def set_pointing_to_coordinate(self, x, y):
        if not self.is_visible():
            self.show()
        self.pointing_to_rectangle.x = x
        self.pointing_to_rectangle.y = y
        self.set_pointing_to(self.pointing_to_rectangle)

    def set_details(self, start: datetime.datetime, stop: datetime.datetime, title1: str, title2: str = None):
        buffer = self.text_box.get_buffer()
        buffer.delete(buffer.get_start_iter(), buffer.get_end_iter())
        text = f"{self._datetime_to_str(start)} - {self._datetime_to_str(stop)}\n"
        text += title1
        if title2 is not None:
            text += f"\n{title2}"
        buffer.set_text(text)

    @staticmethod
    def _datetime_to_str(date: datetime.datetime):
        return f"{date.hour}:{str(date.minute).rjust(2, '0')}:{str(date.second).rjust(2, '0')}"
