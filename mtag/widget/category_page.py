from ..helper import database_helper, statistics_helper, datetime_helper
from ..repository import CategoryRepository

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class CategoryPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, name="category_view")
        self.current_category = None

        self.category_store = Gtk.ListStore(str, int)
        categories_tree_view: Gtk.TreeView = Gtk.TreeView.new_with_model(self.category_store)
        categories_tree_view.connect("button-press-event", self._do_button_press)
        for i, title in enumerate(["Name"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_sort_column_id(i)
            categories_tree_view.append_column(column)

        categories_tree_view.set_headers_clickable(True)
        categories_tree_view.show_all()
        ctw_sw = Gtk.ScrolledWindow()
        ctw_sw.set_size_request(200, -1)
        ctw_sw.add(categories_tree_view)

        self.add(ctw_sw)

        grid = Gtk.Grid()
        grid.set_column_homogeneous(homogeneous=True)
        grid.set_row_spacing(5)
        grid.set_margin_top(5)
        name_title = Gtk.Label(label="Name")
        name_title.set_xalign(0)
        grid.attach(name_title, 0, 0, 1, 1)
        self.name_label = Gtk.Label("-")
        self.name_label.set_xalign(0)
        grid.attach(self.name_label, 1, 0, 2, 1)

        time_tagged_title = Gtk.Label(label="Time tagged")
        time_tagged_title.set_xalign(0)
        grid.attach(time_tagged_title, 0, 1, 1, 1)
        self.total_time_label= Gtk.Label(label="-")
        self.total_time_label.set_xalign(0)
        grid.attach(self.total_time_label, 1, 1, 2, 1)

        url_title = Gtk.Label(label="URL")
        url_title.set_xalign(0)
        grid.attach(url_title, 0, 2, 1, 1)
        self.url_entry= Gtk.Entry()
        grid.attach(self.url_entry, 1, 2, 2, 1)

        save_button = Gtk.Button("Save")
        save_button.connect("clicked", self._do_save_clicked)
        grid.attach(save_button, 2, 4, 1, 1)

        self.pack_end(grid, expand=True, fill=True, padding=20)
        self.show_all()

    def update_page(self):
        conn = database_helper.create_connection()
        categories = CategoryRepository().get_all(conn)
        conn.close()
        self.category_store.clear()
        for c in categories:
            self.category_store.append([c.name, c.db_id])

        self.current_category = None
        self.name_label.set_label("-")
        self.total_time_label.set_label("-")
        self.url_entry.set_text("-")

    def _do_save_clicked(self, w):
        if self.current_category is None:
            return

        cr = CategoryRepository()
        conn = database_helper.create_connection()
        self.current_category.url = self.url_entry.get_text()
        cr.update(conn=conn, category=self.current_category)
        conn.close()

    def _do_button_press(self, w, e):
        item_at_path = w.get_path_at_pos(e.x, e.y)
        if item_at_path is None:
            return

        p, c, *_ = item_at_path
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
