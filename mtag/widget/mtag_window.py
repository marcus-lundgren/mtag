from mtag.helper import database_helper, statistics_helper, datetime_helper
from mtag.repository import CategoryRepository
from mtag.widget.timeline_page import TimelinePage

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

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

        self.connect("destroy", Gtk.main_quit)

        category_view = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.category_store = Gtk.ListStore(str, int)
        categories_tree_view = Gtk.TreeView.new_with_model(self.category_store)
        categories_tree_view.connect("button-press-event", self._do_button_press)
        for i, title in enumerate(["Name"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_sort_column_id(i)
            categories_tree_view.append_column(column)

        conn = database_helper.create_connection()
        categories = CategoryRepository().get_all(conn)
        conn.close()
        for c in categories:
            self.category_store.append([c.name, c.db_id])
        categories_tree_view.set_headers_clickable(True)
        categories_tree_view.show_all()
        category_view.add(categories_tree_view)

        category_details = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title = Gtk.Label(label="== Details ==")
        category_details.pack_start(title, expand=False, fill=False, padding=10)
        self.current_category = None

        grid = Gtk.Grid()
        name_title = Gtk.Label(label="Name: ")
        name_title.set_xalign(0)
        grid.attach(name_title, 0, 0, 1, 1)
        self.name_label = Gtk.Label("-")
        self.name_label.set_xalign(0)
        grid.attach(self.name_label, 1, 0, 1, 1)

        time_tagged_title = Gtk.Label(label="Time tagged: ")
        time_tagged_title.set_xalign(0)
        grid.attach(time_tagged_title, 0, 1, 1, 1)
        self.total_time_label= Gtk.Label(label="-")
        self.total_time_label.set_xalign(0)
        grid.attach(self.total_time_label, 1, 1, 2, 1)

        url_title = Gtk.Label(label="URL: ")
        url_title.set_xalign(0)
        grid.attach(url_title, 0, 2, 1, 1)
        self.url_entry= Gtk.Entry()
        grid.attach(self.url_entry, 1, 2, 2, 1)

        save_button = Gtk.Button("Save")
        save_button.connect("clicked", self._do_save_clicked)
        grid.attach(save_button, 0, 3, 2, 1)
        category_details.add(grid)

        category_view.pack_end(category_details, expand=True, fill=True, padding=20)

        outer_nb = Gtk.Notebook()

        timeline_page = TimelinePage(parent=self)
        outer_nb.append_page(timeline_page, Gtk.Label(label="Timeline"))
        outer_nb.append_page(category_view, Gtk.Label(label="Categories"))
        self.add(outer_nb)
        self.show_all()

    def _do_save_clicked(self, w):
        if self.current_category is None:
            return

        cr = CategoryRepository()
        conn = database_helper.create_connection()
        self.current_category.url = self.url_entry.get_text()
        cr.update(conn=conn, category=self.current_category)
        conn.close()

    def _do_button_press(self, w, e):
        p, c, *_ = w.get_path_at_pos(e.x, e.y)
        i = self.category_store.get_iter(p)
        v = self.category_store.get_value(i, 1)
        self._update_details_pane(v)

    def _update_details_pane(self, category_db_id: int):
        cr = CategoryRepository()
        conn = database_helper.create_connection()
        category = cr.get(conn=conn, db_id=category_db_id)
        conn.close()
        self.current_category = category
        seconds = statistics_helper.get_total_category_tagged_time(category.name)
        h, m, s = datetime_helper.seconds_to_hour_minute_second(seconds)
        total_time_str = f"{h} hours, {m} minutes, {s} seconds"
        self.name_label.set_label(category.name)
        self.total_time_label.set_label(total_time_str)
        self.url_entry.set_text(category.url)
