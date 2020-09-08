import datetime

from mtag.widget.calendar import Calendar

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GObject


class CalendarButton(Gtk.Button):
    @GObject.Signal(name="day-selected",
                    flags=GObject.SignalFlags.RUN_LAST,
                    return_type=GObject.TYPE_BOOLEAN,
                    arg_types=(object,))
    def day_selected(self, *args):
        pass

    def __init__(self):
        super().__init__(stock=None)

        self.calendar = Calendar()
        self.calendar.connect("day-selected-single-click", self._date_selected)
        today_button = Gtk.Button(label="Today")
        today_button.connect("clicked", self._do_today_button_clicked)

        self.calendar_popover = Gtk.Popover()
        self.calendar_popover.set_relative_to(self)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.pack_start(today_button, True, False, 0)
        vbox.pack_start(self.calendar, True, True, 0)
        self.calendar_popover.add(vbox)

        self.connect("clicked", self._show_popup)

        self._update_label()

    def add_days(self, days: int):
        year, month, day = self.calendar.get_date()
        selected_date = datetime.datetime(year=year, month=month + 1, day=day)
        new_date = selected_date + datetime.timedelta(days=days)
        self.calendar.select_month(new_date.month - 1, new_date.year)
        self.calendar.select_day(new_date.day)
        self._update_label()

    def get_selected_date(self):
        return self.calendar.get_date_as_datetime()

    def _show_popup(self, _):
        self.calendar_popover.show_all()
        self.calendar_popover.popup()

    def _do_today_button_clicked(self, _):
        today = datetime.date.today()
        self.calendar.select_month(today.month - 1, today.year)
        self.calendar.select_day(today.day)
        selected_date = self.get_selected_date()
        self._date_selected(None, selected_date)

    def _date_selected(self, _, selected_date):
        self.calendar_popover.popdown()
        self._update_label()
        self.emit("day-selected", selected_date)

    def _update_label(self):
        date = self.calendar.get_date_as_datetime()
        date_as_str = date.strftime("%a %b %e")
        self.set_label(date_as_str)
