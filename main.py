import gi
import cairo
from entity.application import Application
from entity.category import Category
from entity.loggedentry import LoggedEntry
from entity.taggedentry import TaggedEntry

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk
import datetime
from random import randrange


app_names = ["Word", "Outlook", "Emacs"]
applications = []
for idx, n in enumerate(app_names):
    a = Application(n, idx)
    applications.append(a)

logged_entries = []
current_time = datetime.datetime.fromisoformat("2020-07-14")
current_time += datetime.timedelta(hours=5)
for i in range(0, 5):
    minutes = randrange(30, 240)
    elapsed_time = datetime.timedelta(minutes=minutes)
    a = applications[i % len(applications)]
    e = LoggedEntry(start = current_time, stop=current_time + elapsed_time, application = a, title=f"Window title {i}")
    logged_entries.append(e)
    current_time += elapsed_time

categories = []
category_names = ["development", "support", "management"]
for idx, name in enumerate(category_names):
    c = Category(db_id=idx, name=name)
    categories.append(c)

tagged_entries = []


class GtkSpy(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title = "GtkSpy")
        self.set_default_size(720, 400)
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(b)

        self.rect_start = None, None
        self.current_mouse_pos = 0

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect("draw", self._on_draw)
        self.drawing_area.add_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.drawing_area.connect("motion_notify_event", self._on_motion_notify)
        self.drawing_area.connect("button_press_event", self._on_button_press)
        self.drawing_area.connect("button_release_event", self._on_button_release)

        b.pack_start(self.drawing_area, expand=True, fill=True, padding=0)

        lists_grid = Gtk.Grid()
        lists_grid.set_column_homogeneous(True)
        lists_grid.set_row_homogeneous(True)
        lists_grid.set_column_spacing(20)

        self.tagged_entries_box = Gtk.ListBox()

        # Logged entries list
        logged_entries_list_store = Gtk.ListStore(str, str, str, str)
        for le in logged_entries:
            logged_entries_list_store.append([le.application.name, le.title, le.start.strftime('%Y-%m-%d %H:%M:%S'), le.stop.strftime('%Y-%m-%d %H:%M:%S')])

        self.logged_entries_tree_view = Gtk.TreeView.new_with_model(logged_entries_list_store)

        for i, title in enumerate(["Application", "Title", "Start", "Stop"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_sort_column_id(i)
            self.logged_entries_tree_view.append_column(column)

        # Tagged entries list
        self.tagged_entries_list_store = Gtk.ListStore(str, str, str)
        for tagged_entry in tagged_entries:
            self._add_tagged_entry_to_list(tagged_entry)

        self.tagged_entries_tree_view = Gtk.TreeView.new_with_model(self.tagged_entries_list_store)
        self.tagged_entries_tree_view.set_headers_clickable(True)

        for i, title in enumerate(["Category", "Start", "Stop"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_sort_column_id(i)
            self.tagged_entries_tree_view.append_column(column)

        self.timeline_side_padding = 13;
        self.timeline_top_padding = 15;
        self.timeline_height = 80;
        self.pixels_per_minute = 2;

        self.current_tagged_entry = None

        self.logged_entries_tree_view.set_headers_clickable(True)

        lists_grid.attach(self.logged_entries_tree_view, 0, 0, 1, 1)
        lists_grid.attach(self.tagged_entries_tree_view, 1, 0, 1, 1)

        b.pack_end(lists_grid, expand=True, fill=True, padding=10)

    def _add_tagged_entry_to_list(self, tagged_entry):
        print(f"Adding new tagged entry to list {tagged_entry.category.name}")
        self.tagged_entries_list_store.append([tagged_entry.category.name, tagged_entry.start.strftime('%Y-%m-%d %H:%M:%S'), tagged_entry.stop.strftime('%Y-%m-%d %H:%M:%S')])

    def _on_motion_notify(self, widget: Gtk.DrawingArea, event):
        if self.current_tagged_entry is not None:
            timeline_x = self._get_timeline_x(event.x, widget)
            stop_date = self._pixel_to_datetime(timeline_x)
            self.current_tagged_entry.stop = stop_date
        self.current_mouse_pos = event.x
        widget.queue_draw()

    def _on_button_press(self, widget, event):
        c = Category(name="Test")
        timeline_x = self._get_timeline_x(event.x, self.drawing_area)
        start_date = self._pixel_to_datetime(timeline_x)
        self.current_tagged_entry = TaggedEntry(category=c, start=start_date, stop=start_date)

    def _on_button_release(self, widget, event: Gdk.EventType):
        # Ensure that an entry is being created.
        if self.current_tagged_entry is None:
            return

        timeline_x = self._get_timeline_x(event.x, self.drawing_area)
        self.current_tagged_entry.stop = self._pixel_to_datetime(timeline_x)

        # Choose category
        list_store = Gtk.ListStore(str)
        for c in categories:
            list_store.append([c.name])

        combobox = Gtk.ComboBox.new_with_model_and_entry(list_store)
        combobox.connect("changed", self._on_category_combobox_changed)
        combobox.set_entry_text_column(0)

        dialog = Gtk.Dialog(title="Choose category", parent=self, destroy_with_parent=True, modal=True)
        dialog.set_default_size(100, 100)
        dialog.vbox.pack_start(combobox, expand=True, fill=True, padding=50)
        dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        combobox.show()
        r = dialog.run()

        print(r)

        if r == Gtk.ResponseType.OK:
            # Set chosen category
            chosen_category_name = self._get_chosen_combobox_value(combobox)
            chosen_category = [c for c in categories if c.name == chosen_category_name]
            if len(chosen_category) == 1:
                chosen_category = chosen_category[0]
            else:
                new_category = Category(name=chosen_category_name, db_id=100)
                categories.append(new_category)
                chosen_category = new_category

            self.current_tagged_entry.category = chosen_category

            print(self._get_chosen_combobox_value(combobox))
            self._add_tagged_entry_to_list(self.current_tagged_entry)
            tagged_entries.append(self.current_tagged_entry)

        self.current_tagged_entry = None
        dialog.destroy()

        self.drawing_area.queue_draw()

    def _on_category_combobox_changed(self, combo: Gtk.ComboBox):
        print(f"Chosen combobox value: {self._get_chosen_combobox_value(combo)}")

    def _get_chosen_combobox_value(self, combo: Gtk.ComboBox):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            return model[tree_iter][0]

        return combo.get_child().get_text()

    def _get_timeline_x(self, mouse_position: float, drawing_area: Gtk.DrawingArea):
        max_timeline_x = drawing_area.get_allocated_size()[0].width - self.timeline_side_padding - 0.00001
        min_timeline_x = self.timeline_side_padding

        timeline_x = max(mouse_position, min_timeline_x)
        timeline_x = min(max_timeline_x, timeline_x)
        return timeline_x


    def _on_draw(self, w: Gtk.DrawingArea, cr: cairo.Context):
        # Get the size
        drawing_area_size, _ = w.get_allocated_size()
        self.timeline_height = drawing_area_size.height * 0.25
        self.timeline_top_padding = drawing_area_size.height * 0.08

        timeline_x = self._get_timeline_x(self.current_mouse_pos, w)

        # Draw the hour lines
        hour_x_offset = (drawing_area_size.width - self.timeline_side_padding * 2) / 24
        for h in range(0, 25):
            # Hour line
            hx = self.timeline_side_padding + hour_x_offset * h
            cr.set_source_rgb(0.5, 0.5, 0.5)
            cr.new_path()
            cr.move_to(hx, 10)
            cr.line_to(hx, drawing_area_size.height - 50) # Make 50 a variable (hourlineLength)
            cr.stroke()

            # Hour text
            hour_string = str(h)
            text_offset = 5 if len(hour_string) == 1 else 10
            cr.move_to(hx - text_offset, drawing_area_size.height - 30)
            cr.set_font_size(16)
            cr.show_text(str(h))

        colors = [0.2, 0.5, 0.7]
        self.pixels_per_minute = (drawing_area_size.width - self.timeline_side_padding * 2) / (24 * 60)
        for idx, le in enumerate(logged_entries):
            start_x = self.pixels_per_minute * (le.start.hour * 60 + le.start.minute) + self.timeline_side_padding
            stop_x = self.pixels_per_minute * (le.stop.hour * 60 + le.stop.minute) + self.timeline_side_padding

            i = idx + 1
            cr.set_source_rgb(colors[i % len(colors)], colors[i % len(colors)], colors[i % len(colors)])
            cr.rectangle(start_x, self.timeline_height + self.timeline_top_padding * 2, stop_x - start_x, self.timeline_height)
            cr.fill()

        for tagged_entry in tagged_entries:
            self._draw_tagged_entry(tagged_entry, cr)

        if self.current_tagged_entry is not None:
            self._draw_tagged_entry(self.current_tagged_entry, cr)

        # Show a guiding line under the mouse cursor
        cr.new_path()
        cr.set_source_rgb(0.7, 0.7, 0.7)
        cr.move_to(timeline_x, 10)
        cr.line_to(timeline_x, drawing_area_size.height - 10)
        cr.stroke()

    def _draw_tagged_entry(self, tagged_entry: TaggedEntry, cr: cairo.Context):
        start_x = self.pixels_per_minute * (tagged_entry.start.hour * 60 + tagged_entry.start.minute) + self.timeline_side_padding
        stop_x = self.pixels_per_minute * (tagged_entry.stop.hour * 60 + tagged_entry.stop.minute) + self.timeline_side_padding

        cr.set_source_rgb(0, 1, 0)
        if tagged_entry.category is not None:
            color_string = tagged_entry.category.color_rgb
            color = Gdk.color_parse(spec=color_string)
            cr.set_source_rgb(color.red_float, color.green_float, color.blue_float)
        cr.rectangle(start_x, self.timeline_top_padding, stop_x - start_x, self.timeline_height)
        cr.fill()

    def _pixel_to_datetime(self, x_position: int) -> datetime:
        total_minutes = (x_position - self.timeline_side_padding) / self.pixels_per_minute
        hours = total_minutes // 60
        minutes = int(total_minutes % 60)
        stop_date = datetime.datetime.fromisoformat("2020-07-14")
        stop_date += datetime.timedelta(hours=hours, minutes=minutes)
        return stop_date


w = GtkSpy()
w.show_all()
w.connect("destroy", Gtk.main_quit)
Gtk.main()

