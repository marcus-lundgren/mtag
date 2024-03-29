from ..entity import TaggedEntry, Category
from ..helper import statistics_helper, datetime_helper, database_helper
from ..repository import CategoryRepository
from typing import List, Tuple, Optional

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk


class CategoryChoiceDialog(Gtk.Dialog):
    MAIN_SUB_SEPARATOR: str = ">>"

    def __init__(self, window: Gtk.Window, tagged_entry: TaggedEntry):
        super().__init__(title="Choose category", parent=window, destroy_with_parent=True, modal=True)
        self.set_size_request(400, 400)
        self.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self.vbox.set_margin_start(10)
        self.vbox.set_margin_end(10)
        self.vbox.set_margin_top(10)
        self.vbox.set_margin_bottom(10)

        time_text = datetime_helper.to_time_text(tagged_entry.start, tagged_entry.stop, tagged_entry.duration)
        time_text_label = Gtk.Label(label=time_text)

        self.vbox.pack_start(time_text_label, expand=False, fill=False, padding=0)

        self.search_box = Gtk.Entry()
        self.search_box.connect("changed", self._do_entry_changed)
        self.search_box.connect("key_release_event", self._do_key_pressed)

        self.vbox.pack_start(self.search_box, expand=False, fill=False, padding=10)

        self.list_store = Gtk.ListStore(str)
        self.tree_model_filter: Gtk.TreeModelFilter = self.list_store.filter_new()
        self.tree_model_filter.set_visible_func(self._filter_func)

        with database_helper.create_connection() as conn:
            category_repository = CategoryRepository()
            categories = category_repository.get_all(conn=conn)

        for (c_main, c_subs) in categories:
            self.list_store.append([f"{c_main.name}"])
            for c_sub in c_subs:
                self.list_store.append([f"{c_main.name} {CategoryChoiceDialog.MAIN_SUB_SEPARATOR} {c_sub.name}"])

        self.categories_tree_view: Gtk.TreeView = Gtk.TreeView.new_with_model(self.tree_model_filter)
        self.categories_tree_view.connect("button-press-event", self._do_button_press)
        self.categories_tree_view.show_all()
        cat_tree_selection: Gtk.TreeSelection = self.categories_tree_view.get_selection()
        cat_tree_selection.set_mode(Gtk.SelectionMode.SINGLE)
        cat_tree_selection.connect("changed", self._do_selection_changed)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Category", renderer, text=0)
        column.set_sort_column_id(0)
        self.categories_tree_view.append_column(column)

        swctv = Gtk.ScrolledWindow()
        swctv.add(self.categories_tree_view)
        swctv.set_size_request(-1, -1)
        swctv.show_all()
        self.vbox.pack_start(swctv, expand=True, fill=True, padding=10)

        total_time_title_label = Gtk.Label(label="Total previously tagged time")
        self.total_tagged_time_label = Gtk.Label(label="")
        self.vbox.pack_start(total_time_title_label, expand=False, fill=True, padding=0)
        self.vbox.pack_start(self.total_tagged_time_label, expand=False, fill=True, padding=0)
        self.show_all()

    def get_chosen_category_value(self) -> Tuple[str, Optional[str]]:
        main, sub = self.search_box.get_text().strip(), None
        if CategoryChoiceDialog.MAIN_SUB_SEPARATOR in main:
            main, sub = main.split(sep=CategoryChoiceDialog.MAIN_SUB_SEPARATOR, maxsplit=1)
            main, sub = main.strip(), sub.strip()

        return main, sub

    def _do_selection_changed(self, selection: Gtk.TreeSelection, *_):
        _, selected = selection.get_selected()

        # Ensure that we have a valid selection
        if selected is None:
            return

        selected_category = self.tree_model_filter.get_value(selected, 0)
        self.search_box.set_text(selected_category)

    def _do_button_press(self, w: Gtk.TreeView, e: Gdk.EventButton):
        if e.type == Gdk.EventType.DOUBLE_BUTTON_PRESS:
            path = w.get_path_at_pos(e.x, e.y)
            if path is not None:
                self.response(Gtk.ResponseType.OK)

    def _do_entry_changed(self, _):
        self._update_statistics()
        self.tree_model_filter.refilter()

    def _update_statistics(self):
        main_name, sub_name = self.get_chosen_category_value()
        total_time = statistics_helper.get_total_category_tagged_time(main_name=main_name, sub_name=sub_name)
        hours, minutes, seconds = datetime_helper.seconds_to_hour_minute_second(total_seconds=total_time)
        self.total_tagged_time_label.set_label(f"{hours} hours, {minutes} minutes, {seconds} seconds")

    def _do_key_pressed(self, _, e: Gdk.EventKey):
        if e.keyval == Gdk.KEY_Return and len(self.search_box.get_text()) > 0:
            self.response(Gtk.ResponseType.OK)

    def _filter_func(self, model, p_iter, _):
        text = self.search_box.get_text()
        if text == "":
            return True

        return text.lower() in model[p_iter][0].lower()
