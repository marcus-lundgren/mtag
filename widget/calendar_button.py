import gi
from widget.calendar import Calendar

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

        self.calendar_popover = Gtk.Popover()
        self.calendar_popover.set_relative_to(self)
        self.calendar_popover.add(self.calendar)

        self.connect("clicked", self._show_popup)

        self._update_label()

    def get_selected_date(self):
        return self.calendar.get_date_as_datetime()

    def _show_popup(self, _):
        self.calendar_popover.show_all()
        self.calendar_popover.popup()

    def _date_selected(self, _, selected_date):
        self.calendar_popover.popdown()
        self._update_label()
        self.emit("day-selected", selected_date)

    def _update_label(self):
        date_as_str = self.calendar.get_date_as_str()
        self.set_label(date_as_str)
