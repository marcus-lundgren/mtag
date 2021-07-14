import datetime
from collections import namedtuple
from typing import List, Optional

from mtag.entity import LoggedEntry, TaggedEntry
from mtag.helper import color_helper, datetime_helper

import gi
import cairo

from mtag.widget import TimelineCanvas


gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk


TooltipAttributes = namedtuple("TooltipAttributes", ["time_texts", "description_texts", "activity_text", "is_active",
                                                     "text_heights", "x", "y", "width", "height"])


class TimelineOverlay(Gtk.DrawingArea):
    def __init__(self, timeline_canvas: TimelineCanvas):
        super().__init__()
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK
                        | Gdk.EventMask.BUTTON_PRESS_MASK
                        | Gdk.EventMask.BUTTON_RELEASE_MASK
                        | Gdk.EventMask.SCROLL_MASK
                        | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect("draw", self._do_draw)
        self.connect("motion_notify_event", self._on_motion_notify)
        self.connect("button-release-event", self._do_button_release)
        self.connect("button-press-event", self._do_button_press)
        self.connect("scroll_event", self._do_scroll_event)
        self.connect("leave-notify-event", self._do_leave_notify_event)

        self.timeline_canvas = timeline_canvas
        self.current_moused_datetime = datetime.datetime.now()
        self.actual_mouse_pos = {"x": 0, "y": 0}
        self.tooltip_attributes = None
        self.dirty_rectangles = []
        self.moused_over_entity = None

    def _do_scroll_event(self, _, e: Gdk.EventScroll):
        # Zoom in or out
        if e.direction == Gdk.ScrollDirection.UP or e.direction == Gdk.ScrollDirection.DOWN:
            x_to_use = self.actual_mouse_pos["x"]
            dt = self.timeline_canvas.timeline_helper.pixel_to_datetime(x_to_use)
            zoom_in = e.direction == Gdk.ScrollDirection.UP
            self.timeline_canvas.zoom(zoom_in, dt)
            self._update_state(e.x, e.y)
        # Move right or left
        elif e.direction == Gdk.ScrollDirection.RIGHT or e.direction == Gdk.ScrollDirection.LEFT:
            move_right = e.direction == Gdk.ScrollDirection.RIGHT
            self.timeline_canvas.move(move_right)
            self._update_state(e.x, e.y)

    def _do_button_release(self, *_):
        self.timeline_canvas.do_button_release()

    def _do_button_press(self, _, e: Gdk.EventButton):
        self.timeline_canvas.do_button_press(e, self.current_moused_datetime)

    def _do_leave_notify_event(self, *_):
        self.moused_over_entity = None
        self.tooltip_attributes = None
        self.current_moused_datetime = None
        self.queue_draw()

    def _do_draw(self, _, cr: cairo.Context):
        height = self.get_allocated_height()
        width = self.get_allocated_width()
        timeline_canvas = self.timeline_canvas

        # Show a guiding line under the mouse
        if self.current_moused_datetime is not None:
            timeline_x = timeline_canvas.timeline_helper.datetime_to_pixel(self.current_moused_datetime)

            cr.set_source_rgb(0.55, 0.55, 0.55)
            cr.new_path()
            cr.move_to(timeline_x, 0)
            cr.line_to(timeline_x, height)
            cr.stroke()

            current_guidingline_rectangle = cairo.RectangleInt(int(timeline_x) - 2, 0, 4, height)
            self.dirty_rectangles.append(current_guidingline_rectangle)

        # Highlight the hovered over entry
        moused_entry = None if self.moused_over_entity is None else self.moused_over_entity.entry
        if type(moused_entry) is LoggedEntry:
            le = self.moused_over_entity
            cr.set_source_rgba(0.7, 0.7, 0.7, 0.2)
            cr.rectangle(le.start_x, timeline_canvas.le_start_y, le.width, timeline_canvas.timeline_height)
            cr.fill()
        elif type(moused_entry) is TaggedEntry:
            te = self.moused_over_entity
            cr.set_source_rgba(0.7, 0.7, 0.7, 0.2)
            cr.rectangle(te.start_x, timeline_canvas.te_start_y, te.width, timeline_canvas.timeline_height)
            cr.fill()

        # Show the tooltip
        if self.tooltip_attributes is not None:
            self._show_details_tooltip(self.tooltip_attributes, cr)
        return True

    def _on_motion_notify(self, _, e: Gdk.EventMotion):
        self._update_state(e.x, e.y)

    def _update_state(self, mouse_x: float, mouse_y: float):
        timeline_canvas = self.timeline_canvas
        timeline_helper = timeline_canvas.timeline_helper
        current_moused_dt = timeline_helper.pixel_to_datetime(mouse_x)
        next_moused_datetime = current_moused_dt

        canvas_height = self.get_allocated_height()
        canvas_width = self.get_allocated_width()

        current_tagged_entry = timeline_canvas.current_tagged_entry
        current_tagged_entry_dirty_rectangle = None
        if current_tagged_entry is not None:
            datetime_used = timeline_canvas.set_tagged_entry_stop_date(current_moused_dt,
                                                                       current_tagged_entry,
                                                                       timeline_canvas.tagged_entries)
            start_x = int(timeline_helper.datetime_to_pixel(current_tagged_entry.start))
            stop_x = int(timeline_helper.datetime_to_pixel(current_tagged_entry.stop))
            current_tagged_entry_dirty_rectangle = cairo.RectangleInt(start_x - 5, 0,
                                                                      stop_x - start_x + 10, canvas_height)
            self.dirty_rectangles.append(current_tagged_entry_dirty_rectangle)
            if datetime_used is not None:
                next_moused_datetime = datetime_used
        else:
            for t in self.timeline_canvas.visible_tagged_entries:
                if mouse_x < t.start_x:
                    break
                elif mouse_x <= t.stop_x:
                    start_delta = mouse_x - t.start_x
                    stop_delta = t.stop_x - mouse_x

                    next_moused_datetime = t.entry.start if start_delta < stop_delta else t.entry.stop
                    break

        is_active = None
        for ae in timeline_canvas.visible_activity_entries:
            if ae.start_x <= mouse_x <= ae.stop_x:
                is_active = ae.entry.active
                break

        self.current_moused_datetime = next_moused_datetime
        self.actual_mouse_pos["x"], self.actual_mouse_pos["y"] = mouse_x, mouse_y

        time_texts = [datetime_helper.to_time_str(current_moused_dt)]
        desc_texts = []

        self.moused_over_entity = None
        highlight_rectangle = None

        # Show the current tagged entry time text if relevant
        if current_tagged_entry is not None:
            current_te_time_text = datetime_helper.to_time_text(current_tagged_entry.start, current_tagged_entry.stop,
                                                                current_tagged_entry.stop - current_tagged_entry.start)
            time_texts = [current_te_time_text]

        if timeline_canvas.le_start_y <= mouse_y <= timeline_canvas.le_end_y or current_tagged_entry is not None:
            le = self.timeline_canvas.find_visible_logged_entry_by_x_position(mouse_x)
            if le is not None:
                self.moused_over_entity = le
                if current_tagged_entry is None:
                    time_details = datetime_helper.to_time_text(le.entry.start, le.entry.stop, le.entry.duration)
                    time_texts.append(time_details)
                desc_texts.append(le.entry.application_window.application.name)
                desc_texts.append(le.entry.application_window.title)

                highlight_rectangle = cairo.RectangleInt(int(le.start_x) - 5,
                                                         int(timeline_canvas.le_start_y) - 5,
                                                         int(le.width) + 10,
                                                         int(timeline_canvas.timeline_height) + 10)
                self.dirty_rectangles.append(highlight_rectangle)
        elif timeline_canvas.te_start_y <= mouse_y <= timeline_canvas.te_end_y:
            for te in timeline_canvas.visible_tagged_entries:
                if te.start_x <= mouse_x <= te.stop_x:
                    self.moused_over_entity = te
                    if current_tagged_entry is None:
                        time_details = datetime_helper.to_time_text(te.entry.start, te.entry.stop, te.entry.duration)
                        time_texts.append(time_details)
                    desc_texts.append(te.entry.category.name)

                    highlight_rectangle = cairo.RectangleInt(int(te.start_x) - 5,
                                                             int(timeline_canvas.te_start_y) - 5,
                                                             int(te.width) + 10,
                                                             int(timeline_canvas.timeline_height) + 10)
                    self.dirty_rectangles.append(highlight_rectangle)
                    break

        window: Gdk.Window = self.get_window()
        cr = window.cairo_create()

        self.tooltip_attributes = self._get_tooltip_attributes(mouse_x, mouse_y, canvas_width, canvas_height,
                                                               cr, time_texts, desc_texts, is_active)
        dirty_new_tooltip_rect = cairo.RectangleInt(int(self.tooltip_attributes.x) - 2,
                                                    int(self.tooltip_attributes.y) - 2,
                                                    int(self.tooltip_attributes.width) + 4,
                                                    int(self.tooltip_attributes.height) + 4)
        self.dirty_rectangles.append(dirty_new_tooltip_rect)

        timeline_x = timeline_helper.datetime_to_pixel(self.current_moused_datetime)
        current_guidingline_rectangle = cairo.RectangleInt(int(timeline_x), 0, 1, canvas_height)
        self.dirty_rectangles.append(current_guidingline_rectangle)

        for r in self.dirty_rectangles:
            self.queue_draw_area(r.x, r.y, r.width, r.height)

        # Prepare the dirty rectangles for the next time.
        self.dirty_rectangles = [current_guidingline_rectangle, dirty_new_tooltip_rect]
        if highlight_rectangle is not None:
            self.dirty_rectangles.append(highlight_rectangle)

        if current_tagged_entry_dirty_rectangle is not None:
            self.dirty_rectangles.append(current_tagged_entry_dirty_rectangle)

    def _get_tooltip_attributes(self, mouse_x: float, mouse_y: float,
                                canvas_width, canvas_height, cr: cairo.Context,
                                time_text_list: List[str], description_text_list: List[str],
                                is_active: Optional[bool]) -> TooltipAttributes:
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
        else:
            activity_text = None

        for t in texts:
            (_, _, width, height, *_) = cr.text_extents(t)
            widths.append(width)
            heights.append(height)

        width_to_use = max(widths) + (padding * 2)
        height_to_use = sum(heights) + (padding * 2) + line_padding * (len(heights) - 1)

        rect_y = min(canvas_height - height_to_use, mouse_y)
        rect_y = max(rect_y, 0)
        x_to_use = min(mouse_x, canvas_width - width_to_use)
        x_to_use = max(x_to_use, 0.0)
        return TooltipAttributes(time_texts=time_text_list, description_texts=description_text_list,
                                 activity_text=activity_text, text_heights=heights, x=x_to_use, y=rect_y,
                                 width=width_to_use, height=height_to_use, is_active=is_active)

    def _show_details_tooltip(self, tooltip_attributes: TooltipAttributes, cr: cairo.Context) -> None:
        cr.set_font_size(16)
        padding = 10
        line_padding = padding / 2
        texts = tooltip_attributes.time_texts.copy()

        for dt in tooltip_attributes.description_texts:
            texts.append(dt)

        if tooltip_attributes.is_active is not None:
            texts.append(tooltip_attributes.activity_text)

        x = tooltip_attributes.x
        y = tooltip_attributes.y

        # Draw rectangle
        cr.set_source_rgba(0.2, 0.2, 0.8, 0.8)
        cr.rectangle(x, y, tooltip_attributes.width, tooltip_attributes.height)
        cr.fill()

        cr.set_source_rgba(0.8, 0.6, 0.2, 0.6)
        cr.rectangle(x, y, tooltip_attributes.width, tooltip_attributes.height)
        cr.stroke()

        # The texts
        number_of_time_texts = len(tooltip_attributes.time_texts)
        number_of_texts = number_of_time_texts + len(tooltip_attributes.description_texts)
        heights = tooltip_attributes.text_heights
        current_y = y + heights[0] + padding
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
                r, g, b = color_helper.activity_to_text_color_floats(tooltip_attributes.is_active)
                cr.set_source_rgb(r, g, b)

            cr.move_to(x + padding, current_y)
            cr.show_text(t)
