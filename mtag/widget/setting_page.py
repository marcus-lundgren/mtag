import gi

from mtag.helper import configuration_helper
from mtag.helper.configuration_helper import Configuration

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class SettingPage(Gtk.Bin):
    def __init__(self):
        super().__init__()
        configuration = configuration_helper.get_configuration()

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_margin_left(10)
        grid.set_margin_right(10)

        # Inactive after idle seconds
        idle_label = Gtk.Label(label="Inactive after idle seconds")
        idle_label.set_xalign(0)
        grid.attach(idle_label, 0, 0, 1, 1)
        adjustment = Gtk.Adjustment(value=configuration.inactive_after_idle_seconds, lower=1, upper=6000,
                                                                 step_incr=1, page_incr=1, page_size=1)
        self.inactive_after_idle_sec = Gtk.SpinButton(adjustment=adjustment)
        self.inactive_after_idle_sec.set_value(adjustment.get_value())
        self.inactive_after_idle_sec.connect("value-changed", self._save_configuration)
        grid.attach(self.inactive_after_idle_sec, 1, 0, 1, 1)

        # Seconds before new entry
        seconds_before_new_entry_label = Gtk.Label(label="Seconds before new entry")
        seconds_before_new_entry_label.set_xalign(0)
        grid.attach(seconds_before_new_entry_label, 0, 1, 1, 1)
        adjustment = Gtk.Adjustment(value=configuration.seconds_before_new_entry,
                                    lower=1, upper=6000,
                                    step_incr=1, page_incr=1, page_size=1)
        self.seconds_before_new_entry = Gtk.SpinButton(adjustment=adjustment)
        self.seconds_before_new_entry.set_value(adjustment.get_value())
        self.seconds_before_new_entry.connect("value-changed", self._save_configuration)
        grid.attach(self.seconds_before_new_entry, 1, 1, 1, 1)

        # Enable/disable logging of application path
        log_application_path_label = Gtk.Label(label="Log application path")
        log_application_path_label.set_xalign(0)
        grid.attach(log_application_path_label, 0, 2, 1, 1)
        self.log_application_path_switch = Gtk.Switch()
        self.log_application_path_switch.set_active(configuration.log_application_path)
        self.log_application_path_switch.connect("state-set", self._save_configuration)
        vbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(self.log_application_path_switch, expand=False, fill=False, padding=0)
        grid.attach(vbox, 1, 2, 1, 1)

        self.add(grid)

    def update_page(self):
        configuration = configuration_helper.get_configuration()
        self.seconds_before_new_entry.set_value(configuration.seconds_before_new_entry)
        self.inactive_after_idle_sec.set_value(configuration.inactive_after_idle_seconds)
        self.log_application_path_switch.set_active(configuration.log_application_path)

    def _save_configuration(self, *_):
        sec_before_new_entry = int(self.seconds_before_new_entry.get_value())
        inactive_after_idle_sec = int(self.inactive_after_idle_sec.get_value())
        log_app_path = self.log_application_path_switch.get_active()
        configuration = Configuration(inactive_after_idle_seconds=inactive_after_idle_sec,
                                      seconds_before_new_entry=sec_before_new_entry,
                                      log_application_path=log_app_path)
        configuration_helper.update_configuration(configuration)
