import gi

from mtag.widget import CalendarButton

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject


class CalendarPanel(Gtk.Box):
    @GObject.Signal(name="day-selected",
                    flags=GObject.SignalFlags.RUN_LAST,
                    return_type=GObject.TYPE_BOOLEAN,
                    arg_types=(object,))
    def day_selected(self, *args):
        pass

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.calendar_button = CalendarButton()

        one_week_back_button = Gtk.Button(label="<< -1 week")
        one_week_back_button.connect("clicked", self._add_days, -7)
        one_week_forward_button = Gtk.Button(label="+1 week >>")
        one_week_forward_button.connect("clicked", self._add_days, 7)

        one_day_back_button = Gtk.Button(label="< -1 day")
        one_day_back_button.connect("clicked", self._add_days, -1)
        one_day_forward_button = Gtk.Button(label="+1 day >")
        one_day_forward_button.connect("clicked", self._add_days, 1)

        self.pack_start(one_week_back_button, False, False, 0)
        self.pack_start(one_day_back_button, False, False, 0)
        self.pack_start(self.calendar_button, True, True, 0)
        self.pack_start(one_day_forward_button, False, False, 0)
        self.pack_start(one_week_forward_button, False, False, 0)

        self.calendar_button.connect("day-selected", lambda w, d: self.emit("day-selected", d))

    def _add_days(self, _, days):
        self.calendar_button.add_days(days)
        self.emit("day-selected", self.calendar_button.get_selected_date())

    def get_selected_date(self):
        return self.calendar_button.get_selected_date()
