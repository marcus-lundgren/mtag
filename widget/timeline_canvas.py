import datetime

import entity
from helper import color_helper, datetime_helper, database_helper, timeline_helper
from widget.category_choice_dialog import CategoryChoiceDialog
from repository.category_repository import CategoryRepository

import cairo
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject


class TimelineCanvas(Gtk.DrawingArea):
    @GObject.Signal(name="tagged-entry-created",
                    flags=GObject.SignalFlags.RUN_LAST,
                    return_type=GObject.TYPE_BOOLEAN,
                    arg_types=(object,))
    def tagged_entry_created(self, *args):
        pass

    def __init__(self, parent: Gtk.Window):
        super().__init__()
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK
                        | Gdk.EventMask.BUTTON_PRESS_MASK
                        | Gdk.EventMask.BUTTON_RELEASE_MASK
                        | Gdk.EventMask.SCROLL_MASK)
        self.connect("draw", self._do_draw)
        self.connect("motion_notify_event", self._on_motion_notify)
        self.connect("button_press_event", self._on_button_press)
        self.connect("button_release_event", self._on_button_release)
        self.connect("scroll_event", self._do_scroll_event)

        self.parent = parent

        self.current_mouse_pos = 0
        self.actual_mouse_pos = {"x": 0, "y": 0}

        self.timeline_side_padding = 13
        self.timeline_top_padding = 10
        self.timeline_height = 80
        self.pixels_per_seconds = 2

        self.timeline_start = datetime.datetime.now()
        self.timeline_delta = datetime.timedelta(hours=23, minutes=59, seconds=59)

        self.category_repository = CategoryRepository()

        self._current_date = None
        self.current_tagged_entry = None
        self.tagged_entries = []
        self.logged_entries = []

        self.menu = Gtk.Menu()
        self.menu.attach_to_widget(self)
        menu_delete_item = Gtk.ImageMenuItem(Gtk.STOCK_DELETE)
        self.menu.append(menu_delete_item)
        self.menu.show_all()

    def _do_scroll_event(self, _, e: Gdk.EventScroll):
        mouse_datetime = self._pixel_to_datetime(self.actual_mouse_pos["x"])
        mouse_delta = mouse_datetime - self.timeline_start
        mouse_relative_position = mouse_delta.total_seconds() / self.timeline_delta.total_seconds()

        # Zoom in
        if e.direction == Gdk.ScrollDirection.UP:
            if self.timeline_delta.total_seconds() >= (30 * 60):
                old_relative_mouse_pos_in_seconds = mouse_relative_position * self.timeline_delta.total_seconds()
                self.timeline_delta -= datetime.timedelta(minutes=15)
                new_relative_mouse_pos_in_seconds = int(self.timeline_delta.total_seconds() * mouse_relative_position)

                seconds_to_add_to_start = old_relative_mouse_pos_in_seconds - new_relative_mouse_pos_in_seconds
                hour, minute, second = datetime_helper.seconds_to_hour_minute_second(seconds_to_add_to_start)
                delta_to_add = datetime.timedelta(hours=hour, minutes=minute, seconds=second)
                self.timeline_start += delta_to_add
        # Zoom out
        elif e.direction == Gdk.ScrollDirection.DOWN:
            if self.timeline_delta.total_seconds() < (24 * 60 * 60 - 1):
                old_relative_mouse_pos_in_seconds = mouse_relative_position * self.timeline_delta.total_seconds()
                self.timeline_delta += datetime.timedelta(minutes=15)
                if 24 * 60 * 60 - 1 <= self.timeline_delta.total_seconds():
                    self.timeline_delta = datetime.timedelta(hours=23, minutes=59, seconds=59)
                    self.timeline_start = self._current_date
                else:
                    new_relative_mouse_pos_in_seconds = int(self.timeline_delta.total_seconds() * mouse_relative_position)
                    seconds_to_add_to_start = old_relative_mouse_pos_in_seconds - new_relative_mouse_pos_in_seconds
                    hour, minute, second = datetime_helper.seconds_to_hour_minute_second(seconds_to_add_to_start)
                    delta_to_add = datetime.timedelta(hours=hour, minutes=minute, seconds=second)
                    self.timeline_start += delta_to_add

                # Ensure that we don't get too far to the left
                if self.timeline_start < self._current_date:
                    self.timeline_start = self._current_date

                # Ensure that we don't get too far to the right
                if (self.timeline_start + self.timeline_delta).day != self._current_date.day:
                    self.timeline_start = self._current_date + datetime.timedelta(days=1) - self.timeline_delta
        # Move right
        elif e.direction == Gdk.ScrollDirection.RIGHT:
            self.timeline_start += datetime.timedelta(minutes=8)
            # Ensure that we don't get too far to the right
            if (self.timeline_start + self.timeline_delta).day != self._current_date.day:
                self.timeline_start = self._current_date.replace(hour=23, minute=59, second=59) - self.timeline_delta
        # Move left
        elif e.direction == Gdk.ScrollDirection.LEFT:
            self.timeline_start -= datetime.timedelta(minutes=8)
            # Ensure that we don't get too far to the left
            if self.timeline_start < self._current_date:
                self.timeline_start = self._current_date
        self.queue_draw()

    def set_entries(self, dt: datetime.datetime, logged_entries, tagged_entries):
        self.logged_entries = logged_entries
        self.tagged_entries = tagged_entries
        self._current_date = dt

        self.timeline_start = self._current_date
        self.timeline_delta = datetime.timedelta(hours=23, minutes=59, seconds=59)
        self._update_timeline_stop()

        self.queue_draw()

    def _update_timeline_stop(self):
        self.timeline_end = self.timeline_start + self.timeline_delta

    def _do_draw(self, _, cr: cairo.Context):
        # Get the size
        drawing_area_size, _ = self.get_allocated_size()
        (_, _, _, hour_text_height, _, _) = cr.text_extents("1")
        hour_text_and_line_gap = 10

        self.timeline_height = (drawing_area_size.height - self.timeline_top_padding * 3 - hour_text_height - hour_text_and_line_gap) / 2
        self.pixels_per_seconds = (drawing_area_size.width - self.timeline_side_padding * 2) / (self.timeline_delta.total_seconds())

        self.te_start_y = self.timeline_top_padding
        self.te_end_y = self.te_start_y + self.timeline_height

        self.le_start_y = self.te_end_y + self.timeline_top_padding
        self.le_end_y = self.le_start_y + self.timeline_height

        # Draw the hour lines
        for h in range(0, 24):
            # Hour line
            current_date_with_current_hour = self._current_date + datetime.timedelta(hours=h)
            if current_date_with_current_hour < self.timeline_start or self.timeline_end < current_date_with_current_hour:
                continue

            hx = self._datetime_to_pixel(current_date_with_current_hour)

            cr.set_source_rgb(0.5, 0.5, 0.5)
            cr.new_path()
            cr.move_to(hx, self.timeline_top_padding / 2)
            cr.line_to(hx, drawing_area_size.height - hour_text_height - hour_text_and_line_gap)
            cr.stroke()

            # Hour text
            cr.set_font_size(16)
            hour_string = str(h)
            (tx, _, hour_text_width, _, dx, _) = cr.text_extents(hour_string)
            cr.move_to(hx - tx - (hour_text_width / 2), drawing_area_size.height)
            cr.show_text(hour_string)

        for le in self.logged_entries:
            if le.stop < self.timeline_start or self.timeline_end < le.start:
                continue

            start_x = self._datetime_to_pixel(le.start)
            stop_x = self._datetime_to_pixel(le.stop)

            color_string = color_helper.to_color(le.application_window.application.name)
            color = Gdk.color_parse(spec=color_string)
            cr.set_source_rgb(color.red_float, color.green_float, color.blue_float)
            cr.rectangle(start_x, self.le_start_y,
                         stop_x - start_x, self.timeline_height)
            cr.fill()

        for tagged_entry in self.tagged_entries:
            if tagged_entry.stop < self.timeline_start or self.timeline_end < tagged_entry.start:
                continue

            self._draw_tagged_entry(tagged_entry, cr)

        if self.current_tagged_entry is not None:
            start_x = self._datetime_to_pixel(self.current_tagged_entry.start)
            stop_x = self._datetime_to_pixel(self.current_tagged_entry.stop)
            cr.set_source_rgba(0.2, 0.2, 0.2, 0.4)
            cr.rectangle(start_x, 0,
                         stop_x - start_x, drawing_area_size.height)
            cr.fill()

        # Show a guiding line under the mouse cursor
        timeline_x = self._get_timeline_x(self.current_mouse_pos)
        cr.new_path()
        cr.set_source_rgb(0.7, 0.7, 0.7)
        cr.move_to(timeline_x, 10)
        cr.line_to(timeline_x, drawing_area_size.height - 10)
        cr.stroke()

        pixel_as_datetime = self._pixel_to_datetime(self.actual_mouse_pos["x"])
        moused_over_time_string = datetime_helper.to_time_str(pixel_as_datetime)
        time_texts = [moused_over_time_string]
        desc_texts = []

        if self.current_tagged_entry is not None:
            time_details = datetime_helper.to_time_text(self.current_tagged_entry.start,
                                                        self.current_tagged_entry.stop,
                                                        self.current_tagged_entry.duration)
            time_texts = [time_details]
        elif self.te_start_y <= self.actual_mouse_pos["y"] <= self.te_end_y:
            for te in self.tagged_entries:
                if self._datetime_to_pixel(te.stop) < self.actual_mouse_pos["x"]:
                    continue
                elif self.actual_mouse_pos["x"] < self._datetime_to_pixel(te.start):
                    break
                else:
                    time_details = datetime_helper.to_time_text(te.start, te.stop, te.duration)
                    time_texts.append(time_details)
                    desc_texts.append(te.category.name)

                    te_start_x = self._datetime_to_pixel(te.start)
                    te_stop_x = self._datetime_to_pixel(te.stop)
                    cr.set_source_rgba(0.7, 0.7, 0.7, 0.2)
                    cr.rectangle(te_start_x, self.te_start_y,
                                 te_stop_x - te_start_x, self.te_end_y - self.te_start_y)
                    cr.fill()
                    break

        if self.le_start_y <= self.actual_mouse_pos["y"] <= self.le_end_y:
            for le in self.logged_entries:
                if self._datetime_to_pixel(le.stop) < self.actual_mouse_pos["x"]:
                    continue
                elif self.actual_mouse_pos["x"] < self._datetime_to_pixel(le.start):
                    break
                else:
                    if self.current_tagged_entry is None:
                        time_details = datetime_helper.to_time_text(le.start, le.stop, le.duration)
                        time_texts.append(time_details)
                    desc_texts.append(le.application_window.application.name)
                    desc_texts.append(le.application_window.title)

                    le_start_x = self._datetime_to_pixel(le.start)
                    le_stop_x = self._datetime_to_pixel(le.stop)
                    cr.set_source_rgba(0.7, 0.7, 0.7, 0.2)
                    cr.rectangle(le_start_x, self.le_start_y,
                                 le_stop_x - le_start_x, self.le_end_y - self.le_start_y)
                    cr.fill()
                    break

        self._show_details_tooltip(mouse_x=self.actual_mouse_pos["x"],
                                   mouse_y=self.actual_mouse_pos["y"],
                                   canvas_width=drawing_area_size.width,
                                   canvas_height=drawing_area_size.height,
                                   cr=cr,
                                   time_text_list=time_texts,
                                   description_text_list=desc_texts)

    def _show_details_tooltip(self, mouse_x: float, mouse_y: float,
                              canvas_width, canvas_height, cr: cairo.Context,
                              time_text_list: list, description_text_list: list):
            cr.set_font_size(16)
            padding = 10
            line_padding = padding / 2

            widths = []
            heights = []
            texts = time_text_list.copy()

            for dt in description_text_list:
                texts.append(dt)

            for t in texts:
                (_, _, width, height, _, _) = cr.text_extents(t)
                widths.append(width)
                heights.append(height)

            width_to_use = max(widths) + (padding * 2)
            height_to_use = sum(heights) + (padding * 2) + line_padding * (len(heights) - 1)

            rect_y = min(canvas_height - height_to_use, mouse_y)
            x_to_use = min(mouse_x, canvas_width - width_to_use)

            # Draw rectangle
            cr.set_source_rgba(0.1, 0.1, 0.8, 0.6)
            cr.rectangle(x_to_use,
                         rect_y,
                         width_to_use,
                         height_to_use)
            cr.fill()

            cr.set_source_rgba(0.8, 0.6, 0.2, 0.6)
            cr.rectangle(x_to_use,
                         rect_y,
                         width_to_use,
                         height_to_use)
            cr.stroke()

            # The texts
            number_of_time_texts = len(time_text_list)
            current_y = rect_y + heights[0] + padding
            for i, t in enumerate(texts):
                if 0 < i:
                    current_y += heights[i - 1] + line_padding

                if number_of_time_texts <= i:
                    cr.set_source_rgb(0.0, 0.9, 0.9)
                else:
                    cr.set_source_rgb(0.9, 0.9, 0.0)

                cr.move_to(x_to_use + padding, current_y)
                cr.show_text(t)

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

    def _on_button_press(self, widget, event: Gdk.EventButton):
        start_date = self._pixel_to_datetime(self.current_mouse_pos)
        self.current_tagged_entry = entity.TaggedEntry(category=None, start=start_date, stop=start_date)

    def _on_button_release(self, widget, event: Gdk.EventType):
        # Ensure that an entry is being created.
        if self.current_tagged_entry is None:
            return

        tagged_entry_to_create = self.current_tagged_entry
        self.current_tagged_entry = None

        stop_date = self._pixel_to_datetime(event.x)
        self._set_tagged_entry_stop_date(stop_date, tagged_entry_to_create, self.tagged_entries)
        if tagged_entry_to_create.start == tagged_entry_to_create.stop:
            return

        # Choose category
        conn = database_helper.create_connection()
        categories = self.category_repository.get_all(conn=conn)
        conn.close()
        dialog = CategoryChoiceDialog(window=self.parent, categories=categories, tagged_entry=tagged_entry_to_create)
        r = dialog.run()
        chosen_category_name = dialog.get_chosen_category_value()
        dialog.destroy()

        print(r)

        if r == Gtk.ResponseType.OK:
            # Set chosen category
            chosen_category = [c for c in categories if c.name.lower() == chosen_category_name.lower()]
            if len(chosen_category) == 1:
                chosen_category = chosen_category[0]
            else:
                new_category = entity.Category(name=chosen_category_name)
                conn = database_helper.create_connection()
                self.category_repository.insert(conn=conn, category=new_category)
                conn.close()
                chosen_category = new_category

            tagged_entry_to_create.category = chosen_category
            self.emit("tagged-entry-created", tagged_entry_to_create)

        self.queue_draw()

    def _on_motion_notify(self, _: Gtk.DrawingArea, event):
        stop_date = self._pixel_to_datetime(event.x)

        next_mouse_pos = event.x
        if self.current_tagged_entry is not None:
            datetime_used = self._set_tagged_entry_stop_date(stop_date,
                                                             self.current_tagged_entry,
                                                             self.tagged_entries)
            if datetime_used is not None:
                next_mouse_pos = self._datetime_to_pixel(datetime_used)
        else:
            for t in self.tagged_entries:
                if t.contains_datetime(stop_date):
                    start_delta = stop_date - t.start
                    stop_delta = t.stop - stop_date

                    datetime_position = t.start if start_delta < stop_delta else t.stop
                    next_mouse_pos = self._datetime_to_pixel(datetime_position)
                    break

        self.current_mouse_pos = next_mouse_pos
        self.actual_mouse_pos["x"], self.actual_mouse_pos["y"] = event.x, event.y
        self.queue_draw()

    def _get_timeline_x(self, mouse_position: float):
        return timeline_helper.to_timeline_x(x_position=mouse_position,
                                             canvas_width=self.get_allocated_width(),
                                             canvas_side_padding=self.timeline_side_padding)

    def _datetime_to_pixel(self, dt: datetime) -> float:
        return timeline_helper.datetime_to_pixel(dt=dt,
                                                 current_date=self._current_date,
                                                 pixels_per_second=self.pixels_per_seconds,
                                                 timeline_side_padding=self.timeline_side_padding,
                                                 timeline_start_datetime=self.timeline_start,
                                                 timeline_stop_datetime=self.timeline_end)

    def _draw_tagged_entry(self, tagged_entry: entity.TaggedEntry, cr: cairo.Context):
        start_x = self._datetime_to_pixel(tagged_entry.start)
        stop_x = self._datetime_to_pixel(tagged_entry.stop)

        cr.set_source_rgb(0, 1, 0)
        if tagged_entry.category is not None:
            color_string = tagged_entry.category.color_rgb
            color = Gdk.color_parse(spec=color_string)
            cr.set_source_rgb(color.red_float, color.green_float, color.blue_float)
        cr.rectangle(start_x, self.te_start_y, stop_x - start_x, self.timeline_height)
        cr.fill()

    def _pixel_to_datetime(self, x_position: float) -> datetime:
        timeline_x = timeline_helper.to_timeline_x(x_position=x_position,
                                                   canvas_width=self.get_allocated_width(),
                                                   canvas_side_padding=self.timeline_side_padding)
        return timeline_helper.pixel_to_datetime(x_position=timeline_x,
                                                 timeline_side_padding=self.timeline_side_padding,
                                                 pixels_per_second=self.pixels_per_seconds,
                                                 current_date=self._current_date,
                                                 timeline_start_datetime=self.timeline_start,
                                                 timeline_stop_datetime=self.timeline_end)
