import datetime
from collections import namedtuple
from typing import List, Optional

import cairo
import gi

from mtag import entity
from mtag.helper import color_helper, database_helper, timeline_helper
from mtag.repository import CategoryRepository
from mtag.widget import CategoryChoiceDialog, TimelineContextPopover

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject


VisibleEntry = namedtuple("VisibleEntry", ["entry", "start_x", "stop_x", "color"])
TimelineTimeline = namedtuple("TimelineTimeline", ["time", "x", "text", "text_extents"])


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
        self.connect("draw", self._do_draw)
        self.connect("configure-event", lambda *_: self._update_canvas_constants())

        self.parent = parent

        self.timeline_side_padding = 28.6
        self.timeline_top_padding = 15
        self.timeline_height = 80
        self.time_guidingline_text_height = 20
        self.time_guidingline_text_width = 44
        self.hour_text_and_line_gap = 10

        self.timeline_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.timeline_delta = datetime.timedelta(hours=23, minutes=59, seconds=59)
        self.timeline_end = None
        self._update_timeline_stop()

        self._current_date = self.timeline_start
        self.current_tagged_entry: Optional[entity.TaggedEntry] = None
        self.tagged_entries: List[entity.TaggedEntry] = []
        self.logged_entries: List[entity.LoggedEntry] = []
        self.activity_entries: List[entity.ActivityEntry] = []

        self.visible_activity_entries: List[VisibleEntry] = []
        self.visible_tagged_entries: List[VisibleEntry] = []
        self.visible_logged_entries: List[VisibleEntry] = []
        self.time_text_extents = {}

        self.context_menu = TimelineContextPopover(relative_to=self)
        self.context_menu.connect("tagged-entry-delete-event", self._do_context_menu_delete)
        self._update_canvas_constants()

    def _do_context_menu_delete(self, _: TimelineContextPopover, te: entity.TaggedEntry) -> None:
        self.emit("tagged-entry-deleted", te)

    def zoom(self, zoom_in: bool, dt: Optional[datetime.datetime] = None) -> None:
        dt_to_use = dt
        if dt_to_use is None:
            middle_x = (self.get_allocated_width() - (self.timeline_side_padding * 2)) / 2
            middle_dt = self.pixel_to_datetime(middle_x)
            dt_to_use = middle_dt

        new_start, new_stop = timeline_helper.zoom(mouse_datetime=dt_to_use,
                                                   boundary_start=self.timeline_start,
                                                   boundary_stop=self.timeline_end,
                                                   zoom_in=zoom_in)
        self.timeline_start = new_start
        self.timeline_delta = new_stop - new_start

        self._update_timeline_stop()
        self._update_canvas_constants()
        self.queue_draw()

    def move(self, move_right: bool) -> None:
        new_start, new_stop = timeline_helper.move(boundary_start=self.timeline_start,
                                                   boundary_stop=self.timeline_end,
                                                   move_right=move_right)
        self.timeline_start = new_start
        self.timeline_delta = new_stop - new_start

        self._update_timeline_stop()
        self._update_canvas_constants()
        self.queue_draw()

    def _update_canvas_constants(self) -> None:
        canvas_height = self.get_allocated_height()
        canvas_width = self.get_allocated_width()

        self.guidingline_on_timeline_start = self.time_guidingline_text_height + (self.timeline_top_padding / 2)

        self.timeline_height = (canvas_height - self.timeline_top_padding * 2 - self.guidingline_on_timeline_start - self.hour_text_and_line_gap) / 2

        self.te_start_y = self.guidingline_on_timeline_start + self.timeline_top_padding
        self.te_end_y = self.te_start_y + self.timeline_height

        self.le_start_y = self.te_end_y + self.timeline_top_padding
        self.le_end_y = self.le_start_y + self.timeline_height

        minute_increment = self._get_current_minute_increment()

        minute_increment_as_delta = datetime.timedelta(minutes=minute_increment)
        timelines_start = self.timeline_start - minute_increment_as_delta
        if timelines_start <= self._current_date:
            timelines_start = self._current_date

        timelines_end = self.timeline_end + minute_increment_as_delta
        if timelines_end.day != self._current_date.day:
            timelines_end = self.timeline_end

        self.visible_activity_entries = [VisibleEntry(ae,
                                                      self.datetime_to_pixel(ae.start, canvas_width),
                                                      self.datetime_to_pixel(ae.stop, canvas_width),
                                                      color_helper.activity_to_color_floats(ae.active))
                                         for ae in self.activity_entries
                                         if timelines_start <= ae.stop and ae.start <= timelines_end]
        self.visible_logged_entries = [VisibleEntry(le,
                                                    self.datetime_to_pixel(le.start, canvas_width),
                                                    self.datetime_to_pixel(le.stop, canvas_width),
                                                    color_helper.to_color_floats(
                                                            le.application_window.application.name))
                                       for le in self.logged_entries
                                       if timelines_start <= le.stop and le.start <= timelines_end]
        self.visible_tagged_entries = [VisibleEntry(te,
                                                    self.datetime_to_pixel(te.start, canvas_width),
                                                    self.datetime_to_pixel(te.stop, canvas_width),
                                                    color_helper.to_color_floats(te.category.name))
                                       for te in self.tagged_entries
                                       if timelines_start <= te.stop and te.start <= timelines_end]

        window: Gdk.Window = self.get_root_window()
        cr: cairo.Context = window.cairo_create()
        cr.set_font_size(16)

        # Start with the current hour, since we want the timelines to be normalized
        # against e.g. 13:00. This needs to be modified if the side padding no longer represents
        # half of the timeline label.
        current_timeline_time = self._current_date + datetime.timedelta(hours=self.timeline_start.hour)
        self.timeline_timelines = []
        while current_timeline_time <= timelines_end:
            if timelines_start <= current_timeline_time:
                text = f"{str(current_timeline_time.hour).rjust(2, '0')}:{str(current_timeline_time.minute).rjust(2, '0')}"
                if text in self.time_text_extents:
                    text_extents = self.time_text_extents[text]
                else:
                    (tx, _, hour_text_width, *_) = cr.text_extents(text)
                    text_extents = (tx, hour_text_width)
                    self.time_text_extents[text] = text_extents
                self.timeline_timelines.append(TimelineTimeline(time=current_timeline_time,
                                                                x=self.datetime_to_pixel(dt=current_timeline_time,
                                                                                         canvas_width=canvas_width),
                                                                text=text,
                                                                text_extents=text_extents))
                current_timeline_time += minute_increment_as_delta
            else:
                current_timeline_time += minute_increment_as_delta
                continue

    def _get_current_minute_increment(self):
        pixels_per_seconds = (self.get_allocated_width() - self.timeline_side_padding * 2) / (self.timeline_delta.total_seconds())
        minute_text_width_with_padding = int((self.time_guidingline_text_width * 1.3 / pixels_per_seconds) / 60)
        if minute_text_width_with_padding > 59:
            minute_increment = int((minute_text_width_with_padding / 60) + 1) * 60
        elif minute_text_width_with_padding > 29:
            minute_increment = 60
        elif minute_text_width_with_padding > 14:
            minute_increment = 30
        elif minute_text_width_with_padding > 9:
            minute_increment = 15
        elif minute_text_width_with_padding > 4:
            minute_increment = 10
        elif minute_text_width_with_padding >= 1:
            minute_increment = 5
        else:
            minute_increment = 1
        return minute_increment

    def set_entries(self, dt: datetime.datetime, logged_entries, tagged_entries, activity_entries) -> None:
        self.logged_entries = logged_entries
        self.tagged_entries = tagged_entries
        self.activity_entries = activity_entries
        self._current_date = dt

        self.timeline_start = self.timeline_start.replace(year=dt.year, month=dt.month, day=dt.day)
        self._update_timeline_stop()

        self._update_canvas_constants()
        self.queue_draw()

    def set_boundaries(self, start: datetime.datetime, stop: datetime.datetime) -> None:
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
        cr.set_font_size(16)
        cr.set_source_rgb(0.4, 0.4, 0.4)
        cr.rectangle(0, 0, canvas_width, self.guidingline_on_timeline_start + 10)
        cr.fill()
        for timeline_timeline in self.timeline_timelines:
            # Hour line
            time = timeline_timeline.time
            if time.minute == 0:
                cr.set_source_rgb(0.5, 0.5, 0.5)
            else:
                cr.set_source_rgb(0.8, 0.8, 0.8)

            hx = timeline_timeline.x
            cr.new_path()
            cr.move_to(hx, self.guidingline_on_timeline_start)
            cr.line_to(hx, drawing_area_height)
            cr.stroke()

            # Hour text
            cr.set_source_rgb(0.8, 0.8, 0.8)
            tx, hour_text_width = timeline_timeline.text_extents
            cr.move_to(hx - tx - (hour_text_width / 2), self.time_guidingline_text_height)
            cr.show_text(timeline_timeline.text)

        # Show the activity as a background for the time area
        for ae in self.visible_activity_entries:
            r, g, b = ae.color
            cr.set_source_rgba(r, g, b, 0.4)
            cr.rectangle(ae.start_x, 0,
                         ae.stop_x - ae.start_x, drawing_area_height)
            cr.fill()

        # Logged entries
        for le in self.visible_logged_entries:
            r, g, b = le.color
            cr.set_source_rgb(r, g, b)
            cr.rectangle(le.start_x, self.le_start_y,
                         le.stop_x - le.start_x, self.timeline_height)
            cr.fill()
            cr.set_source_rgb(0.2, 0.2, 0.8)
            cr.rectangle(le.start_x, self.le_start_y, le.stop_x - le.start_x, 10)
            cr.fill()

        for te in self.visible_tagged_entries:
            cr.set_source_rgb(0, 1, 0)
            r, g, b = te.color
            cr.set_source_rgb(r, g, b)
            cr.rectangle(te.start_x, self.te_start_y, te.stop_x - te.start_x, self.timeline_height)
            cr.fill()
            cr.set_source_rgb(1, 0.64, 0)
            cr.rectangle(te.start_x, self.te_end_y - 10, te.stop_x - te.start_x, 10)
            cr.fill()

        if self.current_tagged_entry is not None:
            start_x = self.datetime_to_pixel(self.current_tagged_entry.start, canvas_width)
            stop_x = self.datetime_to_pixel(self.current_tagged_entry.stop, canvas_width)
            cr.set_source_rgba(0.2, 0.2, 0.2, 0.4)
            cr.rectangle(start_x, 0,
                         stop_x - start_x, drawing_area_height)
            cr.fill()

        # Draw the sides
        cr.set_source_rgba(0.5, 0.5, 0.5, 0.5)
        cr.rectangle(0, 0, self.timeline_side_padding, drawing_area_height)
        cr.fill()
        cr.rectangle(canvas_width - self.timeline_side_padding, 0, canvas_width, drawing_area_height)
        cr.fill()

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

    def do_button_press(self, event: Gdk.EventButton, current_moused_datetime: datetime.datetime):
        if event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS and event.button == Gdk.BUTTON_PRIMARY:
            start_dt = self.timeline_start
            end_dt = self.timeline_end

            for te in self.visible_tagged_entries:
                # Double click should not be possible if we are inside of a TaggedEntry
                if te.entry.contains_datetime(current_moused_datetime):
                    return

                # Update the intervals if necessary
                if start_dt < te.entry.stop < current_moused_datetime:
                    start_dt = te.entry.stop
                elif current_moused_datetime < te.entry.start < end_dt:
                    end_dt = te.entry.start
                    break
            self.current_tagged_entry = entity.TaggedEntry(category=None, start=start_dt, stop=end_dt)
            return

        # Right click
        if event.button == Gdk.BUTTON_SECONDARY:
            # Ensure that we are on the tagged entry timeline
            if self.te_start_y <= event.y <= self.te_end_y:
                for te in self.visible_tagged_entries:
                    if te.start_x <= event.x <= te.stop_x:
                        self.context_menu.popup_at_coordinate(x=event.x, y=event.y, te=te.entry)
                        break
            return

        start_date = current_moused_datetime
        self.current_tagged_entry = entity.TaggedEntry(category=None, start=start_date, stop=start_date)

    def do_button_release(self):
        # Ensure that an entry is being created.
        if self.current_tagged_entry is None:
            return

        tagged_entry_to_create = self.current_tagged_entry

        if tagged_entry_to_create.start == tagged_entry_to_create.stop:
            self.current_tagged_entry = None
            return

        # Choose category
        with database_helper.create_connection() as conn:
            category_repository = CategoryRepository()
            categories = category_repository.get_all(conn=conn)

        dialog = CategoryChoiceDialog(window=self.parent, categories=categories, tagged_entry=tagged_entry_to_create)
        r = dialog.run()
        self.current_tagged_entry = None
        chosen_category_name = dialog.get_chosen_category_value()
        dialog.destroy()

        if r == Gtk.ResponseType.OK:
            # Set chosen category
            chosen_category = [c for c in categories if c.name.lower() == chosen_category_name.lower()]
            if len(chosen_category) == 1:
                chosen_category = chosen_category[0]
            else:
                new_category = entity.Category(name=chosen_category_name)
                with database_helper.create_connection() as conn:
                    new_category.db_id = category_repository.insert(conn=conn, category=new_category)
                chosen_category = new_category

            tagged_entry_to_create.category = chosen_category
            self.emit("tagged-entry-created", tagged_entry_to_create)

        self.queue_draw()

    def datetime_to_pixel(self, dt: datetime, canvas_width: int) -> float:
        return timeline_helper.datetime_to_pixel(dt=dt,
                                                 canvas_width=canvas_width,
                                                 timeline_side_padding=self.timeline_side_padding,
                                                 timeline_start_dt=self.timeline_start,
                                                 timeline_stop_dt=self.timeline_end)

    def pixel_to_datetime(self, x_position: float) -> datetime:
        return timeline_helper.pixel_to_datetime(x_position,
                                                 self.timeline_side_padding,
                                                 self.get_allocated_width(),
                                                 self.timeline_start,
                                                 self.timeline_end)
