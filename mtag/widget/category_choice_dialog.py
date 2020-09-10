from mtag.entity.tagged_entry import TaggedEntry
from mtag.helper import statistics_helper, datetime_helper

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk


class CategoryChoiceDialog(Gtk.Dialog):
    def __init__(self, window: Gtk.Window, categories: list, tagged_entry: TaggedEntry):
        super().__init__(title="Choose category", parent=window, destroy_with_parent=True, modal=True)
        self.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)

        time_text = datetime_helper.to_time_text(tagged_entry.start, tagged_entry.stop, tagged_entry.duration)
        time_text_label = Gtk.Label(label=time_text)

        self.vbox.pack_start(time_text_label, expand=False, fill=False, padding=0)

        list_store = Gtk.ListStore(str)
        for c in categories:
            list_store.append([c.name])

        self.combobox = Gtk.ComboBox.new_with_model_and_entry(list_store)
        self.combobox.connect("changed", self._on_category_combobox_changed)
        self.combobox.connect("key_release_event", self._do_key_pressed)
        self.combobox.set_entry_text_column(0)

        self.vbox.pack_start(self.combobox, expand=False, fill=False, padding=10)

        total_time_title_label = Gtk.Label(label="Total previously tagged time")
        self.total_tagged_time_label = Gtk.Label(label="")
        self.vbox.pack_start(total_time_title_label, expand=False, fill=True, padding=0)
        self.vbox.pack_start(self.total_tagged_time_label, expand=True, fill=True, padding=0)
        self.show_all()

    def _on_category_combobox_changed(self, _: Gtk.ComboBox):
        chosed_category_name = self.get_chosen_category_value()
        total_time = statistics_helper.get_total_category_tagged_time(chosed_category_name)
        hours, minutes, seconds = datetime_helper.seconds_to_hour_minute_second(total_seconds=total_time)
        self.total_tagged_time_label.set_label(f"{hours} hours, {minutes} minutes, {seconds} seconds")
        print(f"Chosen combobox value: {self.get_chosen_category_value()}")

    def _do_key_pressed(self, _, e: Gdk.EventKey):
        if e.keyval == Gdk.KEY_Return and len(self.get_chosen_category_value()) > 0:
            self.response(Gtk.ResponseType.OK)

    def get_chosen_category_value(self):
        tree_iter = self.combobox.get_active_iter()
        if tree_iter is not None:
            model = self.combobox.get_model()
            return model[tree_iter][0]

        return self.combobox.get_child().get_text()
