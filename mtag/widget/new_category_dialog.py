import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk


class NewCategoryDialog(Gtk.Dialog):
    def __init__(self, window: Gtk.Window):
        super().__init__(title="New category", parent=window, destroy_with_parent=True, modal=True)
        # self.set_size_request(400, 400)
        self.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self.vbox.set_margin_start(10)
        self.vbox.set_margin_end(10)
        self.vbox.set_margin_top(10)
        self.vbox.set_margin_bottom(10)

        self.new_category_entry: Gtk.Entry = Gtk.Entry()

        self.vbox.pack_start(Gtk.Label(label="New category"), expand=False, fill=False, padding=0)
        self.vbox.pack_start(self.new_category_entry, expand=False, fill=False, padding=0)
        self.show_all()

    def get_new_category_name(self) -> str:
        return self.new_category_entry.get_text()
