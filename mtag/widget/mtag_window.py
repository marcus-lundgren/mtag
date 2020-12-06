from ..helper import database_helper, statistics_helper, datetime_helper
from ..repository import CategoryRepository
from . import CategoryPage
from . import TimelinePage

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk


class MTagWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="MTag")
        self.set_default_size(720, 500)
        try:
            it = Gtk.IconTheme()
            icon = it.load_icon(Gtk.STOCK_FIND, 256, Gtk.IconLookupFlags.GENERIC_FALLBACK)
            self.set_icon(icon)
        except:
            print("Unable to load window icon")

        css = Gtk.CssProvider()
        css.load_from_data(b"#nb > * { background-color: transparent; } ")
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(screen, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.connect("destroy", Gtk.main_quit)

        outer_nb = Gtk.Notebook()

        timeline_page = TimelinePage(parent=self)
        category_page = CategoryPage()
        outer_nb.set_name("nb")
        outer_nb.append_page(timeline_page, Gtk.Label(label="Timeline"))
        outer_nb.append_page(category_page, Gtk.Label(label="Categories"))
        self.add(outer_nb)
        self.show_all()
