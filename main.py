import datetime

import entity
from helper import color_helper
from helper import database_helper
from widget import CategoryChoiceDialog, TimelineDetailsPopover
from widget import CalendarButton
from repository.logged_entry_repository import LoggedEntryRepository
from repository.category_repository import CategoryRepository

import gi
import cairo
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk


tagged_entries = []


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

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect("draw", self._on_draw)
        self.drawing_area.add_events(Gdk.EventMask.POINTER_MOTION_MASK
                                     | Gdk.EventMask.BUTTON_PRESS_MASK
                                     | Gdk.EventMask.BUTTON_RELEASE_MASK
                                     | Gdk.EventMask.ENTER_NOTIFY_MASK
                                     | Gdk.EventMask.LEAVE_NOTIFY_MASK)
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
        self.logged_entries_list_store = Gtk.ListStore(str, str, str, str)
        self.logged_entries_tree_view = Gtk.TreeView.new_with_model(self.logged_entries_list_store)

        for i, title in enumerate(["Start", "Stop", "Application", "Title"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_sort_column_id(i)
            column.set_expand(title == "Title")
            self.logged_entries_tree_view.append_column(column)

        self._reload_logged_entries_from_date()

        # Tagged entries list
        self.tagged_entries_list_store = Gtk.ListStore(str, str, str)
        for tagged_entry in tagged_entries:
            self._add_tagged_entry_to_list(tagged_entry)

        self.tagged_entries_tree_view = Gtk.TreeView.new_with_model(self.tagged_entries_list_store)
        self.tagged_entries_tree_view.set_headers_clickable(True)

        for i, title in enumerate(["Start", "Stop", "Category"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_sort_column_id(i)
            self.tagged_entries_tree_view.append_column(column)

        self.timeline_side_padding = 13
        self.timeline_top_padding = 15
        self.timeline_height = 80
        self.pixels_per_seconds = 2

        self.current_tagged_entry = None

        self.logged_entries_tree_view.set_headers_clickable(True)

        letw_container = Gtk.ScrolledWindow()
        letw_container.add(self.logged_entries_tree_view)
        lists_grid.attach(letw_container, 0, 0, 1, 1)
        lists_grid.attach(self.tagged_entries_tree_view, 1, 0, 1, 1)

        b.pack_end(lists_grid, expand=True, fill=True, padding=10)

        self.category_repository = CategoryRepository
        self.info_popover = TimelineDetailsPopover(self.drawing_area)

    def _on_new_day_selected(self, _, date: datetime.datetime):
        self._current_date = date
        self._reload_logged_entries_from_date()

    def _reload_logged_entries_from_date(self):
        db_connection = database_helper.create_connection()
        logged_entry_repository = LoggedEntryRepository()

        self.logged_entries = logged_entry_repository.get_all_by_date(db_connection, self._current_date)
        db_connection.close()

        self.logged_entries_list_store.clear()
        for le in self.logged_entries:
            self.logged_entries_list_store.append([le.start.strftime('%H:%M:%S'),
                                                   le.stop.strftime('%H:%M:%S'),
                                                   le.application.name,
                                                   le.title])
        self.logged_entries_tree_view.columns_autosize()

    def _add_tagged_entry_to_list(self, tagged_entry):
        print(f"Adding new tagged entry to list {tagged_entry.category.name}")
        self.tagged_entries_list_store.append([tagged_entry.start.strftime('%H:%M:%S'),
                                               tagged_entry.stop.strftime('%H:%M:%S'),
                                               tagged_entry.category.name])

    def _on_motion_notify(self, widget: Gtk.DrawingArea, event):
        timeline_x = self._get_timeline_x(event.x, widget)
        stop_date = self._pixel_to_datetime(timeline_x)

        next_mouse_pos = event.x
        if self.current_tagged_entry is not None:
            datetime_used = self._set_tagged_entry_stop_date(stop_date,
                                                             self.current_tagged_entry,
                                                             tagged_entries)
            if datetime_used is not None:
                next_mouse_pos = self._datetime_to_pixel(datetime_used)
        else:
            for t in tagged_entries:
                if t.contains_datetime(stop_date):
                    start_delta = stop_date - t.start
                    stop_delta = t.stop - stop_date

                    datetime_position = t.start if start_delta < stop_delta else t.stop
                    next_mouse_pos = self._datetime_to_pixel(datetime_position)
                    break

        # moused_over_le = None
        # for le in self.logged_entries:
        #     if self._datetime_to_pixel(le.stop) < event.x:
        #         continue
        #     elif event.x < self._datetime_to_pixel(le.start):
        #         break
        #     else:
        #         moused_over_le = le
        #         break
        #
        # if moused_over_le is not None:
        #     self.info_popover.set_details(le.start, le.stop, le.title, le.application.name)
        #     self.info_popover.set_pointing_to_coordinate(event.x, event.y)
        # else:
        #     if self.info_popover.is_visible():
        #         self.info_popover.hide()

        self.current_mouse_pos = next_mouse_pos
        widget.queue_draw()

    @staticmethod
    def _set_tagged_entry_stop_date(stop_date: datetime,
                                    tagged_entry: entity.TaggedEntry, tagged_entries: list):
        tagged_entry.stop = stop_date

        creation_is_right = stop_date == tagged_entry.stop
        date_to_use = None
        for t in tagged_entries:
            if creation_is_right:
                if t.start < stop_date and t.stop > tagged_entry.start:
                    date_to_use = t.start
                    break
            else:
                if stop_date < t.stop and t.start < tagged_entry.stop:
                    date_to_use = t.stop

        if date_to_use is not None:
            tagged_entry.stop = date_to_use

        return date_to_use

    def _on_button_press(self, widget, event):
        c = entity.Category(name="Test")
        timeline_x = self._get_timeline_x(self.current_mouse_pos, self.drawing_area)
        start_date = self._pixel_to_datetime(timeline_x)
        self.current_tagged_entry = entity.TaggedEntry(category=c, start=start_date, stop=start_date)

    def _on_button_release(self, widget, event: Gdk.EventType):
        # Ensure that an entry is being created.
        if self.current_tagged_entry is None:
            return

        timeline_x = self._get_timeline_x(event.x, self.drawing_area)
        stop_date = self._pixel_to_datetime(timeline_x)
        self._set_tagged_entry_stop_date(stop_date, self.current_tagged_entry, tagged_entries)
        if self.current_tagged_entry.start == self.current_tagged_entry.stop:
            self.current_tagged_entry = None
            return

        # Choose category
        conn = database_helper.create_connection()
        categories = self.category_repository.get_all(conn=conn)
        conn.close()
        dialog = CategoryChoiceDialog(window=self, categories=categories)
        r = dialog.run()

        print(r)

        if r == Gtk.ResponseType.OK:
            # Set chosen category
            chosen_category_name = dialog.get_chosen_category_value()
            chosen_category = [c for c in categories if c.name.lower() == chosen_category_name.lower()]
            if len(chosen_category) == 1:
                chosen_category = chosen_category[0]
            else:
                new_category = entity.Category(name=chosen_category_name)
                conn = database_helper.create_connection()
                self.category_repository.insert(conn=conn, category=new_category)
                conn.close()
                chosen_category = new_category

            self.current_tagged_entry.category = chosen_category

            print(dialog.get_chosen_category_value())
            self._add_tagged_entry_to_list(self.current_tagged_entry)
            tagged_entries.append(self.current_tagged_entry)
            tagged_entries.sort(key=lambda t: t.start)

        self.current_tagged_entry = None
        dialog.destroy()

        self.drawing_area.queue_draw()

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
            cr.line_to(hx, drawing_area_size.height - 50)  # TODO: Make 50 a variable (hourlineLength)
            cr.stroke()

            # Hour text
            hour_string = str(h)
            text_offset = 5 if len(hour_string) == 1 else 10
            cr.move_to(hx - text_offset, drawing_area_size.height - 30)
            cr.set_font_size(16)
            cr.show_text(str(h))

        self.pixels_per_seconds = (drawing_area_size.width - self.timeline_side_padding * 2) / (24 * 60 * 60)
        for le in self.logged_entries:
            start_x = self._datetime_to_pixel(le.start)
            stop_x = self._datetime_to_pixel(le.stop)

            color_string = color_helper.to_color(le.application.name)
            color = Gdk.color_parse(spec=color_string)
            cr.set_source_rgb(color.red_float, color.green_float, color.blue_float)
            cr.rectangle(start_x, self.timeline_height + self.timeline_top_padding * 2,
                         stop_x - start_x, self.timeline_height)
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

        moused_over_le = None
        for le in self.logged_entries:
            if self._datetime_to_pixel(le.stop) < self.current_mouse_pos:
                continue
            elif self.current_mouse_pos < self._datetime_to_pixel(le.start):
                break
            else:
                moused_over_le = le
                break

        if moused_over_le is not None:
            cr.set_font_size(16)
            datetime_at_cursor = self._pixel_to_datetime(self._get_timeline_x(self.current_mouse_pos, drawing_area=w))
            #time_text = f"{datetime_at_cursor.hour}:{datetime_at_cursor.minute}:{datetime_at_cursor.second}"
            time_text = f"{moused_over_le.application.name} => {moused_over_le.title}"
            (x, y, width, height, dx, dy) = cr.text_extents(time_text)
            cr.set_source_rgba(0.8, 0.8, 0.8, 0.8)
            width_to_use = width + 20
            preliminary_x = self.current_mouse_pos - 10
            x_to_use = min(preliminary_x, drawing_area_size.width - width_to_use)
            cr.rectangle(x_to_use, (drawing_area_size.height / 2) - height - 10, width + 20, height + 20)
            cr.fill()
            cr.move_to(x_to_use + 10, (drawing_area_size.height / 2))
            cr.set_source_rgb(0.0, 0.0, 0.0)
            cr.show_text(time_text)


    def _datetime_to_pixel(self, dt: datetime) -> float:
        hour, minute, second = dt.hour, dt.minute, dt.second
        if dt < self._current_date:
            hour, minute, second = 0, 0, 0
        elif self._current_date + datetime.timedelta(days=1) <= dt:
            hour, minute, second = 23, 59, 59

        return self.pixels_per_seconds * (hour * 60 * 60 + minute * 60 + second) + self.timeline_side_padding

    def _draw_tagged_entry(self, tagged_entry: entity.TaggedEntry, cr: cairo.Context):
        start_x = self._datetime_to_pixel(tagged_entry.start)
        stop_x = self._datetime_to_pixel(tagged_entry.stop)

        cr.set_source_rgb(0, 1, 0)
        if tagged_entry.category is not None:
            color_string = tagged_entry.category.color_rgb
            color = Gdk.color_parse(spec=color_string)
            cr.set_source_rgb(color.red_float, color.green_float, color.blue_float)
        cr.rectangle(start_x, self.timeline_top_padding, stop_x - start_x, self.timeline_height)
        cr.fill()

    def _pixel_to_datetime(self, x_position: int) -> datetime:
        total_seconds = (x_position - self.timeline_side_padding) / self.pixels_per_seconds
        hours = total_seconds // (60 * 60)
        minutes = (total_seconds - hours * 60 * 60) // 60
        seconds = int(total_seconds % 60)
        d = datetime.datetime(year=self._current_date.year,
                              month=self._current_date.month,
                              day=self._current_date.day)
        d += datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
        return d


w = GtkSpy()
w.show_all()
w.connect("destroy", Gtk.main_quit)
Gtk.main()
