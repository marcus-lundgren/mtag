from ..entity import Category
from ..helper import database_helper, statistics_helper, datetime_helper
from ..repository import CategoryRepository
from .new_category_dialog import NewCategoryDialog
from typing import Dict
from collections import namedtuple


import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

CategoryHolder = namedtuple("CategoryHolder", ["main", "subs"])

class CategoryPage(Gtk.Box):
    def __init__(self, parent: Gtk.Window):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, name="category_view")
        self.current_category_holder = None
        self.categories: Dict[int, CategoryHolder] = {}
        self.parent = parent

        # Main category list
        self.category_store = Gtk.ListStore(str, int)
        self.categories_tree_view: Gtk.TreeView = Gtk.TreeView.new_with_model(self.category_store)
        cat_tree_selection: Gtk.TreeSelection = self.categories_tree_view.get_selection()
        cat_tree_selection.set_mode(Gtk.SelectionMode.BROWSE)
        cat_tree_selection.connect("changed", self._do_main_changed)

        for i, title in enumerate(["Main"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_sort_column_id(i)
            self.categories_tree_view.append_column(column)

        self.categories_tree_view.set_headers_clickable(False)
        self.categories_tree_view.show_all()
        ctw_sw = Gtk.ScrolledWindow()
        ctw_sw.set_size_request(200, -1)
        ctw_sw.add(self.categories_tree_view)
        self.add(ctw_sw)

        # Subcategory list
        sub_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sub_category_store = Gtk.ListStore(str, int)
        self.sub_categories_tree_view: Gtk.TreeView = Gtk.TreeView.new_with_model(self.sub_category_store)
        cat_tree_selection: Gtk.TreeSelection = self.sub_categories_tree_view.get_selection()
        cat_tree_selection.set_mode(Gtk.SelectionMode.BROWSE)
        cat_tree_selection.connect("changed", self._do_sub_changed)

        for i, title in enumerate(["Sub"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_sort_column_id(i)
            self.sub_categories_tree_view.append_column(column)

        self.sub_categories_tree_view.set_headers_clickable(False)
        self.sub_categories_tree_view.show_all()
        ctw_sw = Gtk.ScrolledWindow()
        ctw_sw.set_size_request(200, -1)
        ctw_sw.add(self.sub_categories_tree_view)

        new_sub_category_button = Gtk.Button(label="Create new")
        new_sub_category_button.connect("clicked", self._on_new_sub_clicked)

        sub_box.pack_start(ctw_sw, expand=True, fill=True, padding=0)
        sub_box.pack_end(new_sub_category_button, expand=False, fill=False, padding=0)

        self.add(sub_box)

        # Details
        grid = Gtk.Grid()
        grid.set_column_homogeneous(homogeneous=True)
        grid.set_row_spacing(5)
        grid.set_column_spacing(5)
        grid.set_margin_top(5)

        name_title = Gtk.Label(label="Name")
        name_title.set_xalign(1)
        grid.attach(name_title, 0, 0, 1, 1)

        self.cb_name = Gtk.CheckButton(label="Edit")
        self.name_entry = Gtk.Entry()
        self.cb_name.connect("toggled", lambda w: self.name_entry.set_sensitive(w.get_active()))
        self.name_entry.set_text("-")
        self.name_entry.set_sensitive(False)
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        name_box.pack_start(self.name_entry, expand=True, fill=True, padding=0)
        name_box.pack_start(self.cb_name, expand=False, fill=False, padding=0)
        grid.attach(name_box, 1, 0, 2, 1)

        time_tagged_title = Gtk.Label(label="Time tagged")
        time_tagged_title.set_xalign(1)
        grid.attach(time_tagged_title, 0, 1, 1, 1)
        self.total_time_label = Gtk.Label(label="-")
        self.total_time_label.set_xalign(0)
        grid.attach(self.total_time_label, 1, 1, 2, 1)

        url_title = Gtk.Label(label="URL")
        url_title.set_xalign(1)
        grid.attach(url_title, 0, 2, 1, 1)
        self.url_entry = Gtk.Entry()
        self.url_entry.set_tooltip_text("Tags are supported.\n{{date}} will expand to the chosen date as YYYY-MM-DD.")
        grid.attach(self.url_entry, 1, 2, 2, 1)

        grid.attach(Gtk.Label(label=""), 0, 3, 1, 1)

        change_main_title = Gtk.Label(label="Change parent")
        change_main_title.set_xalign(1)
        grid.attach(change_main_title, 0, 4, 1, 1)
        self.parent_list = Gtk.ComboBoxText.new()
        grid.attach(self.parent_list, 1, 4, 2, 1)

        self.cb_delete = Gtk.CheckButton(label="Unlock delete")
        self.delete_button = Gtk.Button(label="Delete")
        self.cb_delete.connect("toggled", lambda w: self.delete_button.set_sensitive(w.get_active()))
        self.delete_button.set_sensitive(False)
        self.delete_button.connect("clicked", self._do_delete_button_clicked)
        delete_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        delete_box.pack_start(self.delete_button, expand=False, fill=False, padding=0)
        delete_box.pack_start(self.cb_delete, expand=False, fill=False, padding=0)
        grid.attach(delete_box, 1, 5, 2, 1)

        save_button = Gtk.Button("Save")
        save_button.connect("clicked", self._do_save_clicked)
        grid.attach(save_button, 2, 6, 1, 1)

        self.pack_end(grid, expand=True, fill=True, padding=20)
        self.show_all()

    def update_page(self):
        # Clear the stores
        self.category_store.clear()
        self.sub_category_store.clear()
        self.categories.clear()

        # Fetch all main categories
        with database_helper.create_connection() as conn:
            categories = CategoryRepository().get_all(conn)

        for c_main, c_subs in categories:
            self.categories[c_main.db_id] = CategoryHolder(c_main, c_subs)

        for key, holder in self.categories.items():
            self.category_store.append([holder.main.name, key])

        # No main categories in the database
        if len(self.categories) == 0:
            self.current_category = None
            self.name_entry.set_text("-")
            self.total_time_label.set_label("-")
            self.url_entry.set_text("-")
            return

        # At least one main category exist
        s: Gtk.TreeSelection = self.categories_tree_view.get_selection()
        s.select_path("0")
        v = self.category_store.get_value(s.get_selected()[1], 1)
        self.current_category_holder = self.categories[v]
        self._update_details_pane_by_row(0)

    def _do_save_clicked(self, _):
        if self.current_category is None:
            return

        chosen_parent_name = self.parent_list.get_active_text()
        if chosen_parent_name is not None:
            for (_, holder) in self.categories.items():
                if holder.main.name == chosen_parent_name:
                    self.current_category.parent_id = holder.main.db_id
                    break

        self.current_category.name = self.name_entry.get_text()
        self.current_category.url = self.url_entry.get_text()

        cr = CategoryRepository()
        with database_helper.create_connection() as conn:
            cr.update(conn=conn, category=self.current_category)

        self.update_page()

    def _on_new_sub_clicked(self, _):
        new_category_dialog = NewCategoryDialog(window=self.parent)
        dialog_response = new_category_dialog.run()
        new_category_name = new_category_dialog.get_new_category_name()
        new_category_dialog.destroy()

        if dialog_response == Gtk.ResponseType.OK:
            with database_helper.create_connection() as conn:
                cr = CategoryRepository()
                cr.insert_sub(conn=conn, name=new_category_name, parent_id=self.current_category_holder.main.db_id)
                self._update_sub_category_list()
                self.update_page()

    def _do_delete_button_clicked(self, _):
        with database_helper.create_connection() as conn:
            CategoryRepository().delete(conn, self.current_category)
        self.update_page()

    def _update_details_pane_by_row(self, row: int):
        i = self.category_store.get_iter(row)
        v = self.category_store.get_value(i, 1)
        self._update_details_pane(v)

    def _do_main_changed(self, selection: Gtk.TreeSelection, *_):
        _, selected = selection.get_selected()

        # Ensure that we have a valid selection
        if selected is None:
            return

        v = self.category_store.get_value(selected, 1)
        self.current_category_holder = self.categories[v]
        self._update_sub_category_list()

    def _do_sub_changed(self, selection: Gtk.TreeSelection, *_):
        _, selected = selection.get_selected()

        # Ensure that we have a valid selection
        if selected is None:
            return

        v = self.sub_category_store.get_value(selected, 1)
        self._update_details_pane(v)

    def _update_sub_category_list(self):
        self.sub_category_store.clear()
        c_main = self.current_category_holder.main
        self.sub_category_store.append(["[Main]", c_main.db_id])
        for c in self.current_category_holder.subs:
            self.sub_category_store.append([c.name, c.db_id])

        # We are guarenteed at least one sub category
        s: Gtk.TreeSelection = self.sub_categories_tree_view.get_selection()
        s.select_path("0")

    def _update_details_pane(self, category_db_id: int):
        cr = CategoryRepository()
        if category_db_id == self.current_category_holder.main.db_id:
            self.current_category = self.current_category_holder.main
        else:
            subs = [c for c in self.current_category_holder.subs if c.db_id == category_db_id]

            # Verify that we've found the category amongst the sub categories.
            # If not, then we've probably gotten an event for the main category
            # we switched from.
            if len(subs) == 1:
                self.current_category = subs[0]
            else:
                return

        seconds = statistics_helper.get_total_category_tagged_time(self.current_category.name)
        h, m, s = datetime_helper.seconds_to_hour_minute_second(seconds)
        total_time_str = f"{h} hours, {m} minutes, {s} seconds"
        self.name_entry.set_text(self.current_category.name)
        self.total_time_label.set_label(total_time_str)
        self.url_entry.set_text(self.current_category.url)
        self.cb_name.set_active(False)
        self.cb_delete.set_active(False)

        self.parent_list.remove_all()
        if self.current_category.parent_id is not None or len(self.categories[self.current_category.db_id].subs) == 0:
            self.parent_list.set_active(True)
            current_main_id = self.current_category_holder.main.db_id
            for (main_id, holder) in self.categories.items():
                if current_main_id != main_id:
                    self.parent_list.append_text(holder.main.name)
        else:
            self.parent_list.set_active(False)

        # Only allow deletions when we don't have any tagged time
        self.cb_delete.set_sensitive(seconds == 0)
