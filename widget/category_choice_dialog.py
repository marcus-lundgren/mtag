from entity.tagged_entry import TaggedEntry

import gi

from helper import datetime_helper

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class CategoryChoiceDialog(Gtk.Dialog):
    def __init__(self, window: Gtk.Window, categories: list, tagged_entry: TaggedEntry):
        super().__init__(title="Choose category", parent=window, destroy_with_parent=True, modal=True)
        self.set_default_size(100, 100)
        self.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)

        time_text = datetime_helper.to_time_text(tagged_entry.start, tagged_entry.stop, tagged_entry.duration)
        time_text_label = Gtk.Label(label=time_text)
        time_text_label.show()

        list_store = Gtk.ListStore(str)
        for c in categories:
            list_store.append([c.name])

        self.combobox = Gtk.ComboBox.new_with_model_and_entry(list_store)
        self.combobox.connect("changed", self._on_category_combobox_changed)
        self.combobox.set_entry_text_column(0)
        self.combobox.show()

        self.vbox.pack_start(time_text_label, expand=True, fill=True, padding=0)
        self.vbox.pack_start(self.combobox, expand=True, fill=True, padding=50)

    def _on_category_combobox_changed(self, _: Gtk.ComboBox):
        print(f"Chosen combobox value: {self.get_chosen_category_value()}")

    def get_chosen_category_value(self):
        tree_iter = self.combobox.get_active_iter()
        if tree_iter is not None:
            model = self.combobox.get_model()
            return model[tree_iter][0]

        return self.combobox.get_child().get_text()
