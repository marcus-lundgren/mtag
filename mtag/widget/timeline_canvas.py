import datetime
from typing import List

from mtag import entity
from mtag.helper import color_helper, datetime_helper, database_helper, timeline_helper
from mtag.repository import CategoryRepository
from mtag.widget import CategoryChoiceDialog, TimelineContextPopover

import cairo
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject


class TimelineCanvas(Gtk.DrawingArea):
    @GObject.Signal(name="tagged-entry-created",
                    flags=GObject.SignalFlags.RUN_LAST,
                    return_type=GObject.TYPE_BOOLEAN,
                    arg_types=[object])
    def tagged_entry_created(self, *args):
        pass

    @GObject.Signal(name="tagged-entry-deleted",
                    flags=GObject.SignalFlags.RUN_LAST,
                    return_type=GObject.TYPE_BOOLEAN,
                    arg_types=[object])
    def tagged_entry_deleted(self, *args):
        pass

    @GObject.Signal(name="timeline-boundary-changed",
                    flags=GObject.SignalFlags.RUN_LAST,
                    return_type=GObject.TYPE_BOOLEAN,
                    arg_types=[object, object])
    def timeline_boundary_changed(self, *args):
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
        self.connect("configure-event", lambda *_: self._update_canvas_constants())

        self.parent = parent

        self.timeline_side_padding = 28.6
        self.timeline_top_padding = 10
        self.timeline_height = 80
        self.time_guidingline_text_height = 12
        self.time_guidingline_text_width = 44
        self.pixels_per_seconds = 2
        self.hour_text_and_line_gap = 10
        self.minute_increment = 0

        self.timeline_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.timeline_delta = datetime.timedelta(hours=23, minutes=59, seconds=59)
        self.timeline_end = None
        self.minute_increment = 60
        self._update_timeline_stop()

        self.current_moused_datetime = self.timeline_start
        self.actual_mouse_pos = {"x": 0, "y": 0}

        self.category_repository = CategoryRepository()

        self._current_date = self.timeline_start
        self.current_tagged_entry = None
        self.tagged_entries = []
        self.logged_entries = []
        self.activity_entries = []

        self.context_menu = TimelineContextPopover(relative_to=self)
        self.context_menu.connect("tagged-entry-delete-event", self._do_context_menu_delete)
        self._update_canvas_constants()

    def _do_context_menu_delete(self, _: TimelineContextPopover, te: entity.TaggedEntry) -> None:
        self.emit("tagged-entry-deleted", te)

    def _do_scroll_event(self, _, e: Gdk.EventScroll):
        mouse_datetime = self._pixel_to_datetime(self.actual_mouse_pos["x"])

        # Zoom in or out
        if e.direction == Gdk.ScrollDirection.UP or e.direction == Gdk.ScrollDirection.DOWN:
            zoom_in = e.direction == Gdk.ScrollDirection.UP
            new_start, new_stop = timeline_helper.zoom(mouse_datetime=mouse_datetime,
                                                       boundary_start=self.timeline_start,
                                                       boundary_stop=self.timeline_end,
                                                       zoom_in=zoom_in)
            self.timeline_start = new_start
            self.timeline_delta = new_stop - new_start
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

        self._update_timeline_stop()
        self._update_canvas_constants()
        self.queue_draw()

    def _update_canvas_constants(self):
        canvas_height = self.get_allocated_height()
        canvas_width = self.get_allocated_width()

        self.timeline_height = (canvas_height - self.timeline_top_padding * 3 - self.time_guidingline_text_height - self.hour_text_and_line_gap) / 3
        self.pixels_per_seconds = (canvas_width - self.timeline_side_padding * 2) / (self.timeline_delta.total_seconds())

        self.te_start_y = self.timeline_top_padding
        self.te_end_y = self.te_start_y + self.timeline_height

        self.ae_start_y = self.te_end_y + self.timeline_top_padding
        self.ae_end_y = self.ae_start_y + self.timeline_height

        self.le_start_y = self.ae_end_y + self.timeline_top_padding
        self.le_end_y = self.le_start_y + self.timeline_height

        minute_increment = int((self.time_guidingline_text_width * 1.2 / self.pixels_per_seconds) / 60)
        if minute_increment > 59:
            minute_increment = int((minute_increment / 60) + 1) * 60
        elif minute_increment > 29:
            minute_increment = 60
        elif minute_increment > 14:
            minute_increment = 30
        elif minute_increment > 9:
            minute_increment = 15
        elif minute_increment > 4:
            minute_increment = 10
        else:
            minute_increment = 5

        self.minute_increment = minute_increment

    def set_entries(self, dt: datetime.datetime, logged_entries, tagged_entries, activity_entries) -> None:
        self.logged_entries = logged_entries
        self.tagged_entries = tagged_entries
        self.activity_entries = activity_entries
        self._current_date = dt

        self.timeline_start = self.timeline_start.replace(year=dt.year, month=dt.month, day=dt.day)
        self._update_timeline_stop()

        self.queue_draw()

    def set_boundaries(self, start: datetime.datetime, stop: datetime.datetime):
        self.timeline_start = start
        self.timeline_end = stop
        self.timeline_delta = stop - start
        self._update_canvas_constants()
        self.queue_draw()

    def _update_timeline_stop(self) -> None:
        self.timeline_end = self.timeline_start + self.timeline_delta
        self.emit("timeline-boundary-changed", self.timeline_start, self.timeline_end)

    def _do_draw(self, _, cr: cairo.Context):
        # Get the size
        drawing_area_height = self.get_allocated_height()

        # Draw the hour lines
        current_time_line_time = self._current_date + datetime.timedelta(hours=self.timeline_start.hour)
        cr.set_font_size(16)
        while current_time_line_time <= self.timeline_end:
            # Hour line
            if current_time_line_time < self.timeline_start:
                current_time_line_time += datetime.timedelta(minutes=self.minute_increment)
                continue

            hx = self._datetime_to_pixel(current_time_line_time)

            cr.set_source_rgb(0.5, 0.5, 0.5)
            cr.new_path()
            cr.move_to(hx, self.timeline_top_padding / 2)
            cr.line_to(hx, drawing_area_height - self.time_guidingline_text_height - self.hour_text_and_line_gap)
            cr.stroke()

            # Hour text
            hour_minute_string = f"{str(current_time_line_time.hour).rjust(2, '0')}:{str(current_time_line_time.minute).rjust(2, '0')}"
            (tx, _, hour_text_width, _, dx, _) = cr.text_extents(hour_minute_string)
            cr.move_to(hx - tx - (hour_text_width / 2), drawing_area_height)
            cr.show_text(hour_minute_string)

            current_time_line_time += datetime.timedelta(minutes=self.minute_increment)

        # Show guiding current actual time line
        now_dt = datetime.datetime.now()
        if now_dt.date() == self._current_date.date():
            current_time_guiding_line_x = self._datetime_to_pixel(now_dt)
            cr.set_source_rgb(0.3, 0.3, 0.3)
            cr.move_to(current_time_guiding_line_x, self.timeline_top_padding)
            cr.line_to(current_time_guiding_line_x, drawing_area_height - self.hour_text_and_line_gap)
            cr.stroke()

        for le in self.logged_entries:
            if le.stop < self.timeline_start:
                continue
            elif self.timeline_end < le.start:
                break

            start_x = self._datetime_to_pixel(le.start)
            stop_x = self._datetime_to_pixel(le.stop)

            r, g, b = color_helper.to_color_floats(le.application_window.application.name)
            cr.set_source_rgb(r, g, b)
            cr.rectangle(start_x, self.le_start_y,
                         stop_x - start_x, self.timeline_height)
            cr.fill()

        for tagged_entry in self.tagged_entries:
            if tagged_entry.stop < self.timeline_start:
                continue
            elif self.timeline_end < tagged_entry.start:
                break

            self._draw_tagged_entry(tagged_entry, cr)

        for ae in self.activity_entries:
            if ae.stop < self.timeline_start:
                continue
            elif self.timeline_end < ae.start:
                break

            start_x = self._datetime_to_pixel(ae.start)
            stop_x = self._datetime_to_pixel(ae.stop)

            r, g, b = color_helper.activity_to_color_floats(ae.active)
            cr.set_source_rgb(r, g, b)
            cr.rectangle(start_x, self.ae_start_y,
                         stop_x - start_x, self.timeline_height)
            cr.fill()

        if self.current_tagged_entry is not None:
            start_x = self._datetime_to_pixel(self.current_tagged_entry.start)
            stop_x = self._datetime_to_pixel(self.current_tagged_entry.stop)
            cr.set_source_rgba(0.2, 0.2, 0.2, 0.4)
            cr.rectangle(start_x, 0,
                         stop_x - start_x, drawing_area_height)
            cr.fill()

        # Show a guiding line under the mouse cursor
        timeline_x = self._datetime_to_pixel(self.current_moused_datetime)
        cr.new_path()
        cr.set_source_rgb(0.7, 0.7, 0.7)
        cr.move_to(timeline_x, 10)
        cr.line_to(timeline_x, drawing_area_height - 10)
        cr.stroke()

        actual_mouse_pos_x = self.actual_mouse_pos["x"]
        pixel_as_datetime = self._pixel_to_datetime(actual_mouse_pos_x)
        moused_over_time_string = datetime_helper.to_time_str(pixel_as_datetime)
        time_texts = [moused_over_time_string]
        desc_texts = []

        if self.current_tagged_entry is not None:
            time_details = datetime_helper.to_time_text(self.current_tagged_entry.start,
                                                        self.current_tagged_entry.stop,
                                                        self.current_tagged_entry.duration)
            time_texts = [time_details]

        actual_mouse_pos_y = self.actual_mouse_pos["y"]
        if self.te_start_y <= actual_mouse_pos_y <= self.te_end_y:
            for te in self.tagged_entries:
                if self._datetime_to_pixel(te.stop) < actual_mouse_pos_x:
                    continue
                elif actual_mouse_pos_x < self._datetime_to_pixel(te.start):
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
        elif self.ae_start_y <= actual_mouse_pos_y <= self.ae_end_y:
            for ae in self.activity_entries:
                if self._datetime_to_pixel(ae.stop) < actual_mouse_pos_x:
                    continue
                elif actual_mouse_pos_x < self._datetime_to_pixel(ae.start):
                    break
                else:
                    if self.current_tagged_entry is None:
                        time_details = datetime_helper.to_time_text(ae.start, ae.stop, ae.duration)
                        time_texts.append(time_details)
                    activity_text = "Active" if ae.active else "Inactive"
                    desc_texts.append(activity_text)

                    ae_start_x = self._datetime_to_pixel(ae.start)
                    ae_stop_x = self._datetime_to_pixel(ae.stop)
                    cr.set_source_rgba(0.7, 0.7, 0.7, 0.2)
                    cr.rectangle(ae_start_x, self.ae_start_y,
                                 ae_stop_x - ae_start_x, self.ae_end_y - self.ae_start_y)
                    cr.fill()
                    break
        elif self.le_start_y <= actual_mouse_pos_y <= self.le_end_y:
            for le in self.logged_entries:
                if self._datetime_to_pixel(le.stop) < actual_mouse_pos_x:
                    continue
                elif actual_mouse_pos_x < self._datetime_to_pixel(le.start):
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

        self._show_details_tooltip(mouse_x=actual_mouse_pos_x,
                                   mouse_y=actual_mouse_pos_y,
                                   canvas_width=self.get_allocated_width(),
                                   canvas_height=drawing_area_height,
                                   cr=cr,
                                   time_text_list=time_texts,
                                   description_text_list=desc_texts)

    def _show_details_tooltip(self, mouse_x: float, mouse_y: float,
                              canvas_width, canvas_height, cr: cairo.Context,
                              time_text_list: List[str], description_text_list: List[str]) -> None:
        cr.set_font_size(16)
        padding = 10
        line_padding = padding / 2

        widths = []
        heights = []
        texts = time_text_list.copy()

        for dt in description_text_list:
            texts.append(dt)

        for t in texts:
            (_, _, width, height, *_) = cr.text_extents(t)
            widths.append(width)
            heights.append(height)

        width_to_use = max(widths) + (padding * 2)
        height_to_use = sum(heights) + (padding * 2) + line_padding * (len(heights) - 1)

        rect_y = min(canvas_height - height_to_use, mouse_y)
        x_to_use = min(mouse_x, canvas_width - width_to_use)
        x_to_use = max(x_to_use, 0.0)

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
            # Add some padding between the lines
            if 0 < i:
                current_y += heights[i - 1] + line_padding

            # The time texts should be in a different color from the other ones
            if number_of_time_texts <= i:
                cr.set_source_rgb(0.9, 0.9, 0.9)
            else:
                cr.set_source_rgb(0.9, 0.9, 0.0)

            cr.move_to(x_to_use + padding, current_y)
            cr.show_text(t)

    @staticmethod
    def _set_tagged_entry_stop_date(stop_date: datetime,
                                    tagged_entry: entity.TaggedEntry,
                                    tagged_entries: List[entity.TaggedEntry]) -> datetime.datetime:
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

    def _on_button_press(self, _: Gtk.DrawingArea, event: Gdk.EventButton):
        if event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS and event.button == Gdk.BUTTON_PRIMARY:
            start_dt = self.timeline_start
            end_dt = self.timeline_end

            for te in self.tagged_entries:
                # Double click should not be possible if we are inside of a TaggedEntry
                if te.contains_datetime(self.current_moused_datetime):
                    return

                # Update the intervals if necessary
                if start_dt < te.stop < self.current_moused_datetime:
                    start_dt = te.stop
                elif self.current_moused_datetime < te.start < end_dt:
                    end_dt = te.start
                    break
            self.current_tagged_entry = entity.TaggedEntry(category=None, start=start_dt, stop=end_dt)
            self.queue_draw()
            return

        # Right click
        if event.button == Gdk.BUTTON_SECONDARY:
            # Ensure that we are on the tagged entry timeline
            if self.te_start_y <= event.y <= self.te_end_y:
                moused_dt = self._pixel_to_datetime(event.x)
                for te in self.tagged_entries:
                    if te.contains_datetime(moused_dt):
                        self.context_menu.popup_at_coordinate(x=event.x, y=event.y, te=te)
                        break
            return

        start_date = self.current_moused_datetime
        self.current_tagged_entry = entity.TaggedEntry(category=None, start=start_date, stop=start_date)

    def _on_button_release(self, _: Gtk.DrawingArea, event: Gdk.EventType):
        # Ensure that an entry is being created.
        if self.current_tagged_entry is None:
            return

        tagged_entry_to_create = self.current_tagged_entry

        if tagged_entry_to_create.start == tagged_entry_to_create.stop:
            self.current_tagged_entry = None
            return

        # Choose category
        conn = database_helper.create_connection()
        categories = self.category_repository.get_all(conn=conn)
        conn.close()
        dialog = CategoryChoiceDialog(window=self.parent, categories=categories, tagged_entry=tagged_entry_to_create)
        r = dialog.run()
        self.current_tagged_entry = None
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
                new_category.db_id = self.category_repository.insert(conn=conn, category=new_category)
                conn.close()
                chosen_category = new_category

            tagged_entry_to_create.category = chosen_category
            self.emit("tagged-entry-created", tagged_entry_to_create)

        self.queue_draw()

    def _on_motion_notify(self, _: Gtk.DrawingArea, event):
        stop_date = self._pixel_to_datetime(event.x)
        next_moused_datetime = stop_date

        if self.current_tagged_entry is not None:
            datetime_used = self._set_tagged_entry_stop_date(stop_date,
                                                             self.current_tagged_entry,
                                                             self.tagged_entries)
            if datetime_used is not None:
                next_moused_datetime = datetime_used
        else:
            for t in self.tagged_entries:
                if stop_date < t.start:
                    break
                elif t.contains_datetime(stop_date):
                    start_delta = stop_date - t.start
                    stop_delta = t.stop - stop_date

                    next_moused_datetime = t.start if start_delta < stop_delta else t.stop
                    break

        self.current_moused_datetime = next_moused_datetime
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
                                                 timeline_start_dt=self.timeline_start,
                                                 timeline_stop_dt=self.timeline_end)

    def _draw_tagged_entry(self, tagged_entry: entity.TaggedEntry, cr: cairo.Context):
        start_x = self._datetime_to_pixel(tagged_entry.start)
        stop_x = self._datetime_to_pixel(tagged_entry.stop)

        cr.set_source_rgb(0, 1, 0)
        if tagged_entry.category is not None:
            r, g, b = color_helper.to_color_floats(tagged_entry.category.name)
            cr.set_source_rgb(r, g, b)
        cr.rectangle(start_x, self.te_start_y, stop_x - start_x, self.timeline_height)
        cr.fill()

    def _pixel_to_datetime(self, x_position: float) -> datetime:
        timeline_x = timeline_helper.to_timeline_x(x_position,
                                                   self.get_allocated_width(),
                                                   self.timeline_side_padding)
        return timeline_helper.pixel_to_datetime(timeline_x,
                                                 self.timeline_side_padding,
                                                 self.pixels_per_seconds,
                                                 self._current_date,
                                                 self.timeline_start,
                                                 self.timeline_end)
