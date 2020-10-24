import datetime
from collections import namedtuple
from typing import List, Optional

from mtag import entity
from mtag.helper import color_helper, datetime_helper, database_helper, timeline_helper
from mtag.repository import CategoryRepository
from mtag.widget import CategoryChoiceDialog, TimelineContextPopover

import cairo
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject


VisibleEntry = namedtuple("VisibleEntry", ["entry", "start_x", "stop_x"])


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
        self.timeline_top_padding = 15
        self.timeline_height = 80
        self.time_guidingline_text_height = 20
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
        # Move right or left
        elif e.direction == Gdk.ScrollDirection.RIGHT or e.direction == Gdk.ScrollDirection.LEFT:
            move_right = e.direction == Gdk.ScrollDirection.RIGHT
            new_start, new_stop = timeline_helper.move(boundary_start=self.timeline_start,
                                                       boundary_stop=self.timeline_end,
                                                       move_right=move_right)
            self.timeline_start = new_start
            self.timeline_delta = new_stop - new_start

        self._update_timeline_stop()
        self._update_canvas_constants()
        self.queue_draw()

    def _update_canvas_constants(self):
        canvas_height = self.get_allocated_height()
        canvas_width = self.get_allocated_width()

        self.guidingline_on_timeline_start = self.time_guidingline_text_height + (self.timeline_top_padding / 2)

        self.timeline_height = (canvas_height - self.timeline_top_padding * 2 - self.guidingline_on_timeline_start - self.hour_text_and_line_gap) / 2
        self.pixels_per_seconds = (canvas_width - self.timeline_side_padding * 2) / (self.timeline_delta.total_seconds())

        self.te_start_y = self.guidingline_on_timeline_start + self.timeline_top_padding
        self.te_end_y = self.te_start_y + self.timeline_height

        self.le_start_y = self.te_end_y + self.timeline_top_padding
        self.le_end_y = self.le_start_y + self.timeline_height

        self.visible_activity_entries = [VisibleEntry(ae,
                                                      self._datetime_to_pixel(ae.start, canvas_width),
                                                      self._datetime_to_pixel(ae.stop, canvas_width))
                                         for ae in self.activity_entries
                                         if self.timeline_start <= ae.stop or ae.start <= self.timeline_end]
        self.visible_logged_entries = [VisibleEntry(le,
                                                    self._datetime_to_pixel(le.start, canvas_width),
                                                    self._datetime_to_pixel(le.stop, canvas_width))
                                       for le in self.logged_entries
                                       if self.timeline_start <= le.stop or le.start <= self.timeline_end]
        self.visible_tagged_entries = [VisibleEntry(te,
                                                    self._datetime_to_pixel(te.start, canvas_width),
                                                    self._datetime_to_pixel(te.stop, canvas_width))
                                       for te in self.tagged_entries
                                       if self.timeline_start <= te.stop or te.start <= self.timeline_end]

        minute_increment = int((self.time_guidingline_text_width * 1.3 / self.pixels_per_seconds) / 60)
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
        elif minute_increment >= 1:
            minute_increment = 5
        else:
            minute_increment = 1

        self.minute_increment = minute_increment

    def set_entries(self, dt: datetime.datetime, logged_entries, tagged_entries, activity_entries) -> None:
        self.logged_entries = logged_entries
        self.tagged_entries = tagged_entries
        self.activity_entries = activity_entries
        self._current_date = dt

        self.timeline_start = self.timeline_start.replace(year=dt.year, month=dt.month, day=dt.day)
        self._update_timeline_stop()

        self._update_canvas_constants()
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
        canvas_width = self.get_allocated_width()

        # Draw the hour lines
        current_time_line_time = self._current_date + datetime.timedelta(hours=self.timeline_start.hour)
        cr.set_font_size(16)
        cr.set_source_rgb(0.4, 0.4, 0.4)
        cr.rectangle(0, 0, canvas_width, self.guidingline_on_timeline_start + 10)
        cr.fill()
        while current_time_line_time <= self.timeline_end:
            # Hour line
            if current_time_line_time < self.timeline_start:
                current_time_line_time += datetime.timedelta(minutes=self.minute_increment)
                continue

            hx = self._datetime_to_pixel(current_time_line_time, canvas_width)

            if current_time_line_time.minute == 0:
                cr.set_source_rgb(0.5, 0.5, 0.5)
            else:
                cr.set_source_rgb(0.8, 0.8, 0.8)

            cr.new_path()
            cr.move_to(hx, self.guidingline_on_timeline_start)
            cr.line_to(hx, drawing_area_height)
            cr.stroke()

            # Hour text
            cr.set_source_rgb(0.8, 0.8, 0.8)
            hour_minute_string = f"{str(current_time_line_time.hour).rjust(2, '0')}:{str(current_time_line_time.minute).rjust(2, '0')}"
            (tx, _, hour_text_width, _, dx, _) = cr.text_extents(hour_minute_string)
            cr.move_to(hx - tx - (hour_text_width / 2), self.time_guidingline_text_height)
            cr.show_text(hour_minute_string)

            current_time_line_time += datetime.timedelta(minutes=self.minute_increment)

        # Show the activity as a background for the time area
        actual_mouse_pos_x = self.actual_mouse_pos["x"]
        is_active = None
        for ae in self.visible_activity_entries:
            if ae.start_x <= actual_mouse_pos_x <= ae.stop_x:
                is_active = ae.entry.active

            r, g, b = color_helper.activity_to_color_floats(ae.entry.active)
            cr.set_source_rgba(r, g, b, 0.4)
            cr.rectangle(ae.start_x, 0,
                         ae.stop_x - ae.start_x, drawing_area_height)
            cr.fill()

        for le in self.visible_logged_entries:
            r, g, b = color_helper.to_color_floats(le.entry.application_window.application.name)
            cr.set_source_rgb(r, g, b)
            cr.rectangle(le.start_x, self.le_start_y,
                         le.stop_x - le.start_x, self.timeline_height)
            cr.fill()

        for te in self.visible_tagged_entries:
            cr.set_source_rgb(0, 1, 0)
            r, g, b = color_helper.to_color_floats(te.entry.category.name)
            cr.set_source_rgb(r, g, b)
            cr.rectangle(te.start_x, self.te_start_y, te.stop_x - te.start_x, self.timeline_height)
            cr.fill()

        if self.current_tagged_entry is not None:
            start_x = self._datetime_to_pixel(self.current_tagged_entry.start, canvas_width)
            stop_x = self._datetime_to_pixel(self.current_tagged_entry.stop, canvas_width)
            cr.set_source_rgba(0.2, 0.2, 0.2, 0.4)
            cr.rectangle(start_x, 0,
                         stop_x - start_x, drawing_area_height)
            cr.fill()

        # Show a guiding line under the mouse cursor
        timeline_x = self._datetime_to_pixel(self.current_moused_datetime, canvas_width)
        cr.new_path()
        cr.set_source_rgb(0.7, 0.7, 0.7)
        cr.move_to(timeline_x, 10)
        cr.line_to(timeline_x, drawing_area_height - 10)
        cr.stroke()

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
            for te in self.visible_tagged_entries:
                if actual_mouse_pos_x < te.start_x:
                    break
                elif actual_mouse_pos_x <= te.stop_x:
                    time_details = datetime_helper.to_time_text(te.entry.start, te.entry.stop, te.entry.duration)
                    time_texts.append(time_details)
                    desc_texts.append(te.entry.category.name)

                    cr.set_source_rgba(0.7, 0.7, 0.7, 0.2)
                    cr.rectangle(te.start_x, self.te_start_y,
                                 te.stop_x - te.start_x, self.te_end_y - self.te_start_y)
                    cr.fill()
                    break
        elif self.le_start_y <= actual_mouse_pos_y <= self.le_end_y:
            for le in self.visible_logged_entries:
                if actual_mouse_pos_x < le.start_x:
                    break
                elif actual_mouse_pos_x <= le.stop_x:
                    if self.current_tagged_entry is None:
                        time_details = datetime_helper.to_time_text(le.entry.start, le.entry.stop, le.entry.duration)
                        time_texts.append(time_details)
                    desc_texts.append(le.entry.application_window.application.name)
                    desc_texts.append(le.entry.application_window.title)

                    cr.set_source_rgba(0.7, 0.7, 0.7, 0.2)
                    cr.rectangle(le.start_x, self.le_start_y,
                                 le.stop_x - le.start_x, self.le_end_y - self.le_start_y)
                    cr.fill()
                    break

        self._show_details_tooltip(mouse_x=actual_mouse_pos_x,
                                   mouse_y=actual_mouse_pos_y,
                                   canvas_width=canvas_width,
                                   canvas_height=drawing_area_height,
                                   cr=cr,
                                   time_text_list=time_texts,
                                   description_text_list=desc_texts,
                                   is_active=is_active)

    def _show_details_tooltip(self, mouse_x: float, mouse_y: float,
                              canvas_width, canvas_height, cr: cairo.Context,
                              time_text_list: List[str], description_text_list: List[str],
                              is_active: Optional[bool]) -> None:
        cr.set_font_size(16)
        padding = 10
        line_padding = padding / 2

        widths = []
        heights = []
        texts = time_text_list.copy()

        for dt in description_text_list:
            texts.append(dt)

        if is_active is not None:
            activity_text = "[## Active ##]" if is_active else "[## Inactive ##]"
            texts.append(activity_text)

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
        cr.set_source_rgba(0.2, 0.2, 0.8, 0.8)
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
        number_of_texts = number_of_time_texts + len(description_text_list)
        current_y = rect_y + heights[0] + padding
        for i, t in enumerate(texts):
            # Add some padding between the lines
            if 0 < i:
                current_y += heights[i - 1] + line_padding

            # The time texts should be in a different color from the other ones
            if i < number_of_time_texts:
                cr.set_source_rgb(0.9, 0.9, 0.0)
            elif i < number_of_texts:
                cr.set_source_rgb(0.9, 0.9, 0.9)
            else:
                r, g, b = color_helper.activity_to_color_floats(is_active)
                cr.set_source_rgb(r, g, b)

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

    def _on_button_release(self, *_):
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

    def _datetime_to_pixel(self, dt: datetime, canvas_width: int) -> float:
        return timeline_helper.datetime_to_pixel(dt=dt,
                                                 canvas_width=canvas_width,
                                                 timeline_side_padding=self.timeline_side_padding,
                                                 timeline_start_dt=self.timeline_start,
                                                 timeline_stop_dt=self.timeline_end)

    def _pixel_to_datetime(self, x_position: float) -> datetime:
        return timeline_helper.pixel_to_datetime(x_position,
                                                 self.timeline_side_padding,
                                                 self.get_allocated_width(),
                                                 self.timeline_start,
                                                 self.timeline_end)
