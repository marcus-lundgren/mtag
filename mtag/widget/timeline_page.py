import datetime
from itertools import groupby
import webbrowser

from mtag.entity import TaggedEntry
from mtag.helper import datetime_helper, database_helper, link_helper
from mtag.repository import LoggedEntryRepository, TaggedEntryRepository, ActivityEntryRepository, CategoryRepository
from . import CalendarPanel, TimelineCanvas, TimelineMinimap, TimelineOverlay

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk


class TimelinePage(Gtk.Box):
    def __init__(self, parent: Gtk.Window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        # Top bar
        self.tagged_time_label = Gtk.Label()
        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.calendar_panel = CalendarPanel()
        self.calendar_panel.connect("day-selected", self._on_new_day_selected)
        self.calendar_panel.set_halign(Gtk.Align.START)
        top_bar.pack_start(self.calendar_panel, expand=True, fill=True, padding=0)
        zoom_to_fit_button = Gtk.Button("Zoom to fit")
        top_bar.pack_start(zoom_to_fit_button, expand=False, fill=False, padding=0)
        top_bar.pack_start(Gtk.Label(label="Tagged time:"), expand=False, fill=False, padding=10)
        top_bar.pack_start(self.tagged_time_label, expand=False, fill=False, padding=10)
        self.pack_start(top_bar, expand=False, fill=False, padding=0)

        self._current_date = self.calendar_panel.get_selected_date()

        # Drawing area
        self.timeline_canvas = TimelineCanvas(parent=parent)
        self.timeline_canvas.connect("tagged-entry-created", self._do_tagged_entry_created)
        self.timeline_canvas.connect("tagged-entry-deleted", self._do_tagged_entry_deleted)
        self.timeline_canvas.connect("timeline-boundary-changed",
                                     lambda _, start, stop: self.timeline_minimap.set_boundaries(start, stop))
        canvas_overlay = Gtk.Overlay()
        canvas_overlay.add_overlay(self.timeline_canvas)
        canvas_overlay.add_overlay(TimelineOverlay(timeline_canvas=self.timeline_canvas))
        zoom_to_fit_button.connect("clicked", lambda *_: self.timeline_canvas.zoom_to_fit())

        self.pack_start(canvas_overlay, expand=True, fill=True, padding=10)

        # Minimap
        self.timeline_minimap = TimelineMinimap()
        self.timeline_minimap.connect("timeline-boundary-changed", lambda _, start, stop: self.timeline_canvas.set_boundaries(start, stop))
        self.add(self.timeline_minimap)

        lists_grid = Gtk.Grid()
        lists_grid.set_column_homogeneous(True)
        lists_grid.set_row_homogeneous(True)
        lists_grid.set_column_spacing(20)

        # Logged entries list
        self.logged_entries_list_store = Gtk.ListStore(str, str, str, str, str)
        self.logged_entries_tree_view = Gtk.TreeView.new_with_model(self.logged_entries_list_store)

        for i, title in enumerate(["Start", "Stop", "Duration", "Application", "Title"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_sort_column_id(i)
            column.set_expand(title == "Title")
            self.logged_entries_tree_view.append_column(column)

        # Tagged entries list
        self.tagged_entries_list_store = Gtk.ListStore(str, str, str)
        self.tagged_entries_tree_view = Gtk.TreeView.new_with_model(self.tagged_entries_list_store)
        self.tagged_entries_tree_view.set_headers_clickable(True)
        self.tagged_entries_tree_view.connect("button-press-event", self._do_button_press_te)

        for i, title in enumerate(["Duration", "Category", "URL"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_sort_column_id(i)
            self.tagged_entries_tree_view.append_column(column)

        self.logged_entries_tree_view.set_headers_clickable(True)

        notebook = Gtk.Notebook()
        notebook.append_page(self.tagged_entries_tree_view, Gtk.Label(label="Tagged entries"))
        letw_container = Gtk.ScrolledWindow()
        letw_container.add(self.logged_entries_tree_view)
        notebook.append_page(letw_container, Gtk.Label(label="Logged entries"))

        self.pack_end(notebook, expand=True, fill=True, padding=10)
        self._reload_logged_entries_from_date()

        self.connect("key-press-event", self._do_key_press_event)
        self.connect("key-release-event", self._do_key_release_event)
        self.show_all()

    def update_page(self):
        self._reload_logged_entries_from_date()

    def _do_key_press_event(self, _, e: Gdk.EventKey):
        # Handle canvas zoom and movement
        if e.state & Gdk.ModifierType.CONTROL_MASK:
            if e.keyval == Gdk.KEY_Up:
                self.timeline_canvas.zoom(True)
            elif e.keyval == Gdk.KEY_Down:
                self.timeline_canvas.zoom(False)
            elif e.keyval == Gdk.KEY_Left:
                self.timeline_canvas.move(False)
            elif e.keyval == Gdk.KEY_Right:
                self.timeline_canvas.move(True)
            return True

    def _do_key_release_event(self, _, e: Gdk.EventKey):
        # Handle date switching
        if e.state & Gdk.ModifierType.MOD1_MASK:
            if e.keyval == Gdk.KEY_Left:
                self.calendar_panel.previous_day()
            elif e.keyval == Gdk.KEY_Right:
                self.calendar_panel.next_day()
            return True

    def _do_button_press_te(self, w: Gtk.TreeView, e):
        if e.type == Gdk.EventType.DOUBLE_BUTTON_PRESS:
            path = w.get_path_at_pos(e.x, e.y)
            if path is None:
                return

            p, c, *_ = path
            i = self.tagged_entries_list_store.get_iter(p)
            v = self.tagged_entries_list_store.get_value(i, 2)

            if v != "":
                webbrowser.open(v)

    def _do_tagged_entry_created(self, _, te: TaggedEntry):
        tagged_entry_repository = TaggedEntryRepository()
        with database_helper.create_connection() as conn:
            tagged_entry_repository.insert(conn=conn, tagged_entry=te)
        self._reload_logged_entries_from_date()

    def _do_tagged_entry_deleted(self, _, te: TaggedEntry):
        tagged_entry_repository = TaggedEntryRepository()
        with database_helper.create_connection() as conn:
            tagged_entry_repository.delete(conn=conn, db_id=te.db_id)
        self._reload_logged_entries_from_date()

    def _on_new_day_selected(self, _, date: datetime.datetime):
        self._current_date = date
        self._reload_logged_entries_from_date()

    def _reload_logged_entries_from_date(self):
        with database_helper.create_connection() as db_connection:
            logged_entry_repository = LoggedEntryRepository()
            tagged_entry_repository = TaggedEntryRepository()
            activity_entry_repository = ActivityEntryRepository()

            logged_entries = logged_entry_repository.get_all_by_date(db_connection, self._current_date)
            tagged_entries = tagged_entry_repository.get_all_by_date(db_connection, self._current_date)
            activity_entries = activity_entry_repository.get_all_by_date(db_connection, self._current_date)

        self.timeline_canvas.set_entries(self._current_date, logged_entries, tagged_entries, activity_entries)
        self.timeline_minimap.set_entries(self._current_date, logged_entries, tagged_entries)

        self.logged_entries_list_store.clear()
        for le in logged_entries:
            self.logged_entries_list_store.append([datetime_helper.to_time_str(le.start),
                                                   datetime_helper.to_time_str(le.stop),
                                                   datetime_helper.to_duration_str(le.duration),
                                                   le.application_window.application.name,
                                                   le.application_window.title])
        self.logged_entries_tree_view.columns_autosize()

        cr = CategoryRepository()
        self.tagged_entries_list_store.clear()
        total_duration = datetime.timedelta()
        for te_category, te_group in groupby(sorted(tagged_entries, key=lambda x: x.category.db_id),
                                             key=lambda x: x.category.name):
            te_list = list(te_group)
            duration = sum([te.duration for te in te_list], start=datetime.timedelta())
            total_duration += duration

            category = te_list[0].category
            expanded_url = link_helper.expand_tags(url=category.url, dt=self._current_date)
            self.tagged_entries_list_store.append([datetime_helper.to_duration_str(duration),
                                                   te_category,
                                                   expanded_url])
        self.tagged_entries_tree_view.columns_autosize()
        self.tagged_time_label.set_label(datetime_helper.to_duration_str(total_duration))
