import datetime

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject


class Calendar(Gtk.Calendar):
    @GObject.Signal(name="day-selected-single-click",
                    flags=GObject.SignalFlags.RUN_LAST,
                    return_type=GObject.TYPE_BOOLEAN,
                    arg_types=[object])
    def day_selected_single_click(self, *args):
        pass

    def __init__(self):
        super().__init__()
        self._last_signal_was_not_single_click = False

        self.set_display_options(Gtk.CalendarDisplayOptions.SHOW_WEEK_NUMBERS
                                 | Gtk.CalendarDisplayOptions.SHOW_HEADING
                                 | Gtk.CalendarDisplayOptions.SHOW_DAY_NAMES)
        self.connect("day-selected", self._on_date_selected)

        self.connect("month-changed", self._register_not_single_click_select)
        self.connect("prev-month", self._register_not_single_click_select)
        self.connect("next-month", self._register_not_single_click_select)
        self.connect("prev-year", self._register_not_single_click_select)
        self.connect("next-year", self._register_not_single_click_select)

    def _register_not_single_click_select(self, _):
        self._last_signal_was_not_single_click = True

    def get_date_as_str(self) -> str:
        year, month, day = self.get_date()
        return f"{year}-{str(month + 1).rjust(2, '0')}-{str(day).rjust(2, '0')}"

    def get_date_as_datetime(self) -> datetime.datetime:
        year, month, day = self.get_date()
        return datetime.datetime(year=year, month=month + 1, day=day)

    def _on_date_selected(self, _) -> None:
        if self._last_signal_was_not_single_click:
            # Reset our signal watching state
            self._last_signal_was_not_single_click = False
        else:
            selected_date = self.get_date_as_datetime()
            self.emit("day-selected-single-click", selected_date)
