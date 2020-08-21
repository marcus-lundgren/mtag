import datetime

from helper import datetime_helper, database_helper
from widget.timeline_canvas import TimelineCanvas
from widget import CalendarButton
from repository.logged_entry_repository import LoggedEntryRepository
from repository.tagged_entry_repository import TaggedEntryRepository

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk


class GtkSpy(Gtk.Window):
    def __init__(self):
        super().__init__(title="GtkSpy")
        self.set_default_size(720, 400)

        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(b)

        # Top bar
        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.calendar_button = CalendarButton()
        self.calendar_button.connect("day-selected", self._on_new_day_selected)
        top_bar.pack_start(self.calendar_button, expand=True, fill=False, padding=0)
        b.add(top_bar)

        self._current_date = self.calendar_button.get_selected_date()

        # Drawing area
        self.current_mouse_pos = 0
        self.actual_mouse_pos = {"x": 0, "y": 0}

        self.timeline_canvas = TimelineCanvas(parent=self)
        self.timeline_canvas.connect("tagged-entry-created", self._do_tagged_entry_created)

        b.pack_start(self.timeline_canvas, expand=True, fill=True, padding=0)

        lists_grid = Gtk.Grid()
        lists_grid.set_column_homogeneous(True)
        lists_grid.set_row_homogeneous(True)
        lists_grid.set_column_spacing(20)

        self.tagged_entries_box = Gtk.ListBox()

        # Logged entries list
        self.logged_entries_list_store = Gtk.ListStore(str, str, str, str)
        self.logged_entries_tree_view = Gtk.TreeView.new_with_model(self.logged_entries_list_store)

        for i, title in enumerate(["Start", "Stop", "Application", "Title"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_sort_column_id(i)
            column.set_expand(title == "Title")
            self.logged_entries_tree_view.append_column(column)

        # Tagged entries list
        self.tagged_entries_list_store = Gtk.ListStore(str, str, str)
        self.tagged_entries_tree_view = Gtk.TreeView.new_with_model(self.tagged_entries_list_store)
        self.tagged_entries_tree_view.set_headers_clickable(True)

        for i, title in enumerate(["Start", "Stop", "Category"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_sort_column_id(i)
            self.tagged_entries_tree_view.append_column(column)

        self.logged_entries_tree_view.set_headers_clickable(True)

        letw_container = Gtk.ScrolledWindow()
        letw_container.add(self.logged_entries_tree_view)
        lists_grid.attach(letw_container, 0, 0, 1, 1)
        lists_grid.attach(self.tagged_entries_tree_view, 1, 0, 1, 1)

        b.pack_end(lists_grid, expand=True, fill=True, padding=10)

        self._reload_logged_entries_from_date()

    def _do_tagged_entry_created(self, _, te):
        tagged_entry_repository = TaggedEntryRepository()
        conn = database_helper.create_connection()
        tagged_entry_repository.insert(conn=conn, tagged_entry=te)
        conn.close()
        self._reload_logged_entries_from_date()

    def _on_new_day_selected(self, _, date: datetime.datetime):
        self._current_date = date
        self._reload_logged_entries_from_date()

    def _reload_logged_entries_from_date(self):
        db_connection = database_helper.create_connection()
        logged_entry_repository = LoggedEntryRepository()
        tagged_entry_repository = TaggedEntryRepository()

        logged_entries = logged_entry_repository.get_all_by_date(db_connection, self._current_date)
        tagged_entries = tagged_entry_repository.get_all_by_date(db_connection, self._current_date)
        db_connection.close()

        self.timeline_canvas.set_entries(self._current_date, logged_entries, tagged_entries)

        self.logged_entries_list_store.clear()
        for le in logged_entries:
            self.logged_entries_list_store.append([datetime_helper.to_time_str(le.start),
                                                   datetime_helper.to_time_str(le.stop),
                                                   le.application.name,
                                                   le.title])
        self.logged_entries_tree_view.columns_autosize()

        self.tagged_entries_list_store.clear()
        for te in tagged_entries:
            self.tagged_entries_list_store.append([datetime_helper.to_time_str(te.start),
                                                   datetime_helper.to_time_str(te.stop),
                                                   te.category.name])
        self.tagged_entries_tree_view.columns_autosize()


w = GtkSpy()
w.show_all()
w.connect("destroy", Gtk.main_quit)
Gtk.main()
