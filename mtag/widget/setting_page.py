import gi

from mtag.helper import configuration_helper

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

        idle_label = Gtk.Label(label="Inactive after idle seconds")
        idle_label.set_xalign(0)
        grid.attach(idle_label, 0, 0, 1, 1)
        adjustment = Gtk.Adjustment(value=configuration.inactive_after_idle_seconds, lower=1, upper=6000, step_incr=1, page_incr=1, page_size=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment)
        spin_button.set_value(adjustment.get_value())
        grid.attach(spin_button, 1, 0, 1, 1)

        seconds_before_new_entry_label = Gtk.Label(label="Seconds before new entry")
        seconds_before_new_entry_label.set_xalign(0)
        grid.attach(seconds_before_new_entry_label, 0, 1, 1, 1)
        adjustment = Gtk.Adjustment(value=configuration.seconds_before_new_entry, lower=1, upper=6000, step_incr=1, page_incr=1, page_size=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment)
        spin_button.set_value(adjustment.get_value())
        grid.attach(spin_button, 1, 1, 1, 1)

        log_application_path_label = Gtk.Label(label="Log application path")
        log_application_path_label.set_xalign(0)
        grid.attach(log_application_path_label, 0, 2, 1, 1)
        switch = Gtk.Switch()
        switch.set_active(configuration.log_application_path)
        vbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(switch, expand=False, fill=False, padding=0)
        grid.attach(vbox, 1, 2, 1, 1)

        self.add(grid)

    def update_page(self):
        pass
