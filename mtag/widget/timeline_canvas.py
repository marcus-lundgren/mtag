import datetime
import math
from collections import namedtuple, defaultdict
from typing import List, Optional, Union, Tuple, DefaultDict

import cairo
import gi

from mtag import entity
from mtag.entity import TaggedEntry, LoggedEntry, ActivityEntry
from mtag.helper import color_helper, database_helper
from mtag.helper.timeline_helper import TimelineHelper
from mtag.repository import CategoryRepository
from mtag.widget import CategoryChoiceDialog, TimelineContextPopover


gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject


TimelineTimeline = namedtuple("TimelineTimeline", ["time", "x", "text", "text_extents"])


class TimelineEntry:
    def __init__(self, entry: Union[TaggedEntry, LoggedEntry, ActivityEntry], color: Tuple):
        self.entry = entry
        self.color = color
        self.start_x = 0
        self.stop_x = 0
        self.width = 0
        self.start_y = 0
        self.height = 0

    def set_x_positions(self, start_x: float, stop_x: float):
        self.start_x = math.floor(start_x)
        self.stop_x = math.ceil(stop_x)
        self.width = self.stop_x - self.start_x

    def set_draw_positions(self, start_x: float, stop_x: float, start_y: float, height: float):
        self.set_x_positions(start_x, stop_x)
        self.start_y = start_y
        self.height = height


class ZoomState:
    MINIMUM_DELTA = datetime.timedelta(seconds=10)

    def __init__(self, initial: datetime.datetime, moving: datetime.datetime):
        self.initial = initial
        self.moving = moving

    def set_moving(self, moving: datetime.datetime) -> None:
        if moving < self.initial:
            if self.initial - moving > ZoomState.MINIMUM_DELTA:
                self.moving = moving
            else:
                self.moving = self.initial - ZoomState.MINIMUM_DELTA
        else:
            if moving - self.initial > ZoomState.MINIMUM_DELTA:
                self.moving = moving
            else:
                self.moving = self.initial + ZoomState.MINIMUM_DELTA

    def get_start(self) -> datetime.datetime:
        return self.initial if self.initial <= self.moving else self.moving

    def get_stop(self) -> datetime.datetime:
        return self.initial if self.initial > self.moving else self.moving


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
        self.timeline_end = self.timeline_start
        self._update_timeline_stop()

        self._current_date = self.timeline_start
        self.current_tagged_entry: Optional[entity.TaggedEntry] = None
        self.tagged_entries: List[TimelineEntry] = []
        self.logged_entries: List[TimelineEntry] = []
        self.activity_entries: List[TimelineEntry] = []

        self.zoom_state: Optional[ZoomState] = None

        self.visible_activity_entries: List[TimelineEntry] = []
        self.visible_tagged_entries: List[TimelineEntry] = []
        self.visible_logged_entries: List[TimelineEntry] = []
        self.time_text_extents = {}

        self.timeline_entries_by_color: DefaultDict = defaultdict(list)

        self.context_menu = TimelineContextPopover(relative_to=self)
        self.context_menu.connect("tagged-entry-delete-event", self._do_context_menu_delete)
        self._update_canvas_constants()

    def _create_timeline_helper(self) -> TimelineHelper:
        return TimelineHelper(canvas_width=self.get_allocated_width(),
                              timeline_start_dt=self.timeline_start,
                              timeline_stop_dt=self.timeline_end,
                              timeline_side_padding=self.timeline_side_padding)

    def _do_context_menu_delete(self, _: TimelineContextPopover, te: entity.TaggedEntry) -> None:
        self.emit("tagged-entry-deleted", te)

    def zoom(self, zoom_in: bool, dt: Optional[datetime.datetime] = None) -> None:
        dt_to_use = dt
        if dt_to_use is None:
            middle_x = (self.get_allocated_width() - (self.timeline_side_padding * 2)) / 2
            middle_dt = self.timeline_helper.pixel_to_datetime(middle_x)
            dt_to_use = middle_dt

        new_start, new_stop = self.timeline_helper.zoom(mouse_datetime=dt_to_use,
                                                        boundary_start=self.timeline_start,
                                                        boundary_stop=self.timeline_end,
                                                        zoom_in=zoom_in)
        self._set_zoom_boundaries(new_start, new_stop)

    def zoom_to_fit(self) -> None:
        number_of_logged_entries = len(self.logged_entries)
        number_of_tagged_entries = len(self.tagged_entries)

        current_date_as_datetime = datetime.datetime(year=self._current_date.year,
                                                     month=self._current_date.month,
                                                     day=self._current_date.day)

        # If we don't have any entries, then show the whole day
        if number_of_logged_entries == 0 and number_of_tagged_entries == 0:
            new_start = current_date_as_datetime
            new_stop = current_date_as_datetime.replace(hour=23, minute=59, second=59)
            self._set_zoom_boundaries(new_start, new_stop)
            return

        # We have at least one entry in the timeline
        starts = []
        stops = []
        if number_of_logged_entries > 0:
            starts.append(self.logged_entries[0].entry.start)
            stops.append(self.logged_entries[number_of_logged_entries - 1].entry.stop)

        if number_of_tagged_entries > 0:
            starts.append(self.tagged_entries[0].entry.start)
            stops.append(self.tagged_entries[number_of_tagged_entries - 1].entry.stop)

        # Choose the earliest start, but ensure that we are within today's date
        new_start = max(current_date_as_datetime, min(starts))

        # Choose the latest stop, but ensure that we are within today's date
        new_stop = min(current_date_as_datetime.replace(hour=23, minute=59, second=59), max(stops))

        self._set_zoom_boundaries(new_start, new_stop)

    def move(self, move_right: bool) -> None:
        new_start, new_stop = self.timeline_helper.move(boundary_start=self.timeline_start,
                                                        boundary_stop=self.timeline_end,
                                                        move_right=move_right)
        self._set_zoom_boundaries(new_start, new_stop)

    def _update_canvas_constants(self) -> None:
        canvas_height = self.get_allocated_height()

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

        # Reset the viewport states
        self.visible_activity_entries.clear()
        self.visible_logged_entries.clear()
        self.visible_tagged_entries.clear()
        self.timeline_entries_by_color.clear()

        self.timeline_helper = self._create_timeline_helper()

        # Gather the visible activity entries
        for ae in self.activity_entries:
            ae_entry = ae.entry
            if ae_entry.stop < timelines_start or timelines_end < ae_entry.start:
                continue

            ae.set_x_positions(self.timeline_helper.datetime_to_pixel(ae_entry.start),
                               self.timeline_helper.datetime_to_pixel(ae_entry.stop))
            self.visible_activity_entries.append(ae)

        # Gather the visible logged entries
        last_stop_x = None
        self.visible_logged_entries = []
        for le in self.logged_entries:
            le_entry = le.entry

            # Ensure that the entry is within the viewport
            if le_entry.stop < timelines_start or timelines_end < le_entry.start:
                continue

            le.set_draw_positions(self.timeline_helper.datetime_to_pixel(le_entry.start),
                                  self.timeline_helper.datetime_to_pixel(le_entry.stop),
                                  self.le_start_y, self.timeline_height)

            # If we end at the same x-position as before, there is no need to draw this entry as it would be hidden
            if le.stop_x != last_stop_x:
                self.visible_logged_entries.append(le)
                self.timeline_entries_by_color[le.color].append(le)
                last_stop_x = le.stop_x

        # Gather the visible tagged entries
        for te in self.tagged_entries:
            te_entry = te.entry
            if te_entry.stop < timelines_start or timelines_end < te_entry.start:
                continue

            te.set_draw_positions(self.timeline_helper.datetime_to_pixel(te_entry.start),
                                  self.timeline_helper.datetime_to_pixel(te_entry.stop),
                                  self.te_start_y, self.timeline_height)
            self.visible_tagged_entries.append(te)
            self.timeline_entries_by_color[te.color].append(te)

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
                                                                x=self.timeline_helper.datetime_to_pixel(current_timeline_time),
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

    def set_entries(self, dt: datetime.datetime, logged_entries: List[LoggedEntry],
                    tagged_entries: List[TaggedEntry], activity_entries: List[ActivityEntry]) -> None:
        self.logged_entries = [TimelineEntry(le, color_helper.to_color_floats(le.application_window.application.name))
                               for le in logged_entries]
        self.tagged_entries = [TimelineEntry(te, color_helper.to_color_floats(te.category_str))
                               for te in tagged_entries]
        self.activity_entries = [TimelineEntry(ae, color_helper.activity_to_color_floats(ae.active))
                                 for ae in activity_entries]
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

        clip_start_x, _, clip_stop_x, _ = cr.clip_extents()

        # Show the activity as a background for the time area
        for ae in self.visible_activity_entries:
            if ae.stop_x < clip_start_x or clip_stop_x < ae.start_x:
                continue

            cr.set_source_rgb(*ae.color)
            cr.rectangle(ae.start_x, 0, ae.width, drawing_area_height)
            cr.fill()

        # Draw the hour lines
        cr.set_font_size(16)
        cr.set_source_rgb(0.35, 0.35, 0.35)
        cr.rectangle(0, 0, canvas_width, self.guidingline_on_timeline_start + 10)
        cr.fill()
        for timeline_timeline in self.timeline_timelines:
            # Hour line
            hx = timeline_timeline.x
            cr.set_source_rgb(0.7, 0.7, 0.7)
            cr.new_path()
            cr.move_to(hx, self.guidingline_on_timeline_start)
            cr.line_to(hx, self.guidingline_on_timeline_start + 10)
            cr.stroke()

            # Hour text
            time = timeline_timeline.time
            if time.minute == 0:
                cr.set_source_rgb(0.9, 0.9, 0.3)
            else:
                cr.set_source_rgb(0.2, 0.8, 1)

            tx, hour_text_width = timeline_timeline.text_extents
            cr.move_to(hx - tx - (hour_text_width / 2), self.time_guidingline_text_height)
            cr.show_text(timeline_timeline.text)

        # Draw the rectangles for the entries by colors
        for color, drawing_entries in self.timeline_entries_by_color.items():
            cr.set_source_rgb(*color)
            for drawing_entry in drawing_entries:
                if drawing_entry.stop_x < clip_start_x or clip_stop_x < drawing_entry.start_x:
                    continue
                cr.rectangle(drawing_entry.start_x, drawing_entry.start_y, drawing_entry.width, drawing_entry.height)
            cr.fill()

        # The marker for the logged entries
        cr.set_source_rgb(0.3, 0.3, 0.8)
        for le in self.visible_logged_entries:
            if le.stop_x < clip_start_x or clip_stop_x < le.start_x:
                continue
            cr.rectangle(le.start_x, self.le_start_y, le.width, 10)
        cr.fill()

        # The marker for the tagged entries
        cr.set_source_rgb(1, 0.64, 0)
        for te in self.visible_tagged_entries:
            if te.stop_x < clip_start_x or clip_stop_x < te.start_x:
                continue
            cr.rectangle(te.start_x, self.te_end_y - 10, te.width, 10)
        cr.fill()

        if self.current_tagged_entry is not None:
            start_x = self.timeline_helper.datetime_to_pixel(self.current_tagged_entry.start)
            stop_x = self.timeline_helper.datetime_to_pixel(self.current_tagged_entry.stop)
            cr.set_source_rgba(0.2, 0.2, 0.2, 0.4)
            cr.rectangle(start_x, 0, stop_x - start_x, drawing_area_height)
            cr.fill()
        elif self.zoom_state is not None:
            start_x = self.timeline_helper.datetime_to_pixel(self.zoom_state.get_start())
            stop_x = self.timeline_helper.datetime_to_pixel(self.zoom_state.get_stop())
            cr.set_source_rgba(0.2, 0.6, 0.2, 0.4)
            cr.rectangle(start_x, 0, stop_x - start_x, drawing_area_height)
            cr.fill()

        # Draw the sides
        cr.set_source_rgba(0.5, 0.5, 0.5, 0.5)
        cr.rectangle(0, 0, self.timeline_side_padding, drawing_area_height)
        cr.fill()
        cr.rectangle(canvas_width - self.timeline_side_padding, 0, canvas_width, drawing_area_height)
        cr.fill()

    @staticmethod
    def set_tagged_entry_stop_date(stop_date: datetime,
                                   tagged_entry: entity.TaggedEntry,
                                   tagged_entries: List[TimelineEntry]) -> datetime.datetime:
        tagged_entry.stop = stop_date

        creation_is_right = stop_date == tagged_entry.stop
        date_to_use = None
        for t in tagged_entries:
            if creation_is_right:
                if t.entry.start < stop_date and t.entry.stop > tagged_entry.start:
                    date_to_use = t.entry.start
                    break
            else:
                if stop_date < t.entry.stop and t.entry.start < tagged_entry.stop:
                    date_to_use = t.entry.stop

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

        # We are beginning a zoom state
        if event.button == Gdk.BUTTON_PRIMARY and event.state & Gdk.ModifierType.SHIFT_MASK:
            moused_dt = self.timeline_helper.pixel_to_datetime(event.x)
            self.zoom_state = ZoomState(moused_dt, moused_dt)
            return

        # We are beginning the creation a new tagged entry
        start_date = current_moused_datetime
        self.current_tagged_entry = entity.TaggedEntry(category=None, start=start_date, stop=start_date)

    def do_button_release(self):
        # Handle the zoom state if relevant
        if self.zoom_state is not None:
            self._set_zoom_boundaries(self.zoom_state.get_start(), self.zoom_state.get_stop())
            self.zoom_state = None
            return

        # Ensure that an entry is being created.
        if self.current_tagged_entry is None:
            return

        tagged_entry_to_create = self.current_tagged_entry

        if tagged_entry_to_create.start == tagged_entry_to_create.stop:
            self.current_tagged_entry = None
            return

        # Choose category
        dialog = CategoryChoiceDialog(window=self.parent, tagged_entry=tagged_entry_to_create)
        r = dialog.run()
        self.current_tagged_entry = None
        (main_category, sub_category) = dialog.get_chosen_category_value()
        dialog.destroy()

        if r == Gtk.ResponseType.OK:
            # Set chosen category
            with database_helper.create_connection() as conn:
                category_repository = CategoryRepository()
                tagged_entry_to_create.category = category_repository.insert(conn=conn, main_name=main_category, sub_name=sub_category)

            self.emit("tagged-entry-created", tagged_entry_to_create)

        self.queue_draw()

    def find_visible_logged_entry_by_x_position(self, x: float) -> Optional[TimelineEntry]:
        number_of_visible_logged_entries = len(self.visible_logged_entries)
        if number_of_visible_logged_entries == 0:
            return None

        current_start = 0
        current_end = number_of_visible_logged_entries - 1
        while current_start <= current_end:
            middle = (current_start + current_end) // 2
            current_entry = self.visible_logged_entries[middle]
            if current_entry.start_x <= x <= current_entry.stop_x:
                return current_entry
            elif x < current_entry.start_x:
                current_end = middle - 1
            else:
                current_start = middle + 1
        return None

    def _set_zoom_boundaries(self, start: datetime.datetime, stop: datetime.datetime):
        self.timeline_start = start
        self.timeline_delta = stop - start
        self._update_timeline_stop()
        self._update_canvas_constants()
        self.queue_draw()
