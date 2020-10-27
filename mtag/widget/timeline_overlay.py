import datetime
from typing import List, Optional

from mtag.helper import color_helper, datetime_helper

import gi
import cairo

from mtag.widget import TimelineCanvas

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk


class TimelineOverlay(Gtk.DrawingArea):
    def __init__(self, timeline_canvas: TimelineCanvas):
        super().__init__()
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK
                        | Gdk.EventMask.BUTTON_PRESS_MASK
                        | Gdk.EventMask.BUTTON_RELEASE_MASK
                        | Gdk.EventMask.SCROLL_MASK)
        self.connect("draw", self._do_draw)
        self.connect("motion_notify_event", self._on_motion_notify)
        self.connect("button-release-event", self._do_button_release)
        self.connect("button-press-event", self._do_button_press)
        self.connect("scroll_event", self._do_scroll_event)

        self.timeline_canvas = timeline_canvas
        self.current_moused_datetime = datetime.datetime.now()
        self.actual_mouse_pos = {"x": 0, "y": 0}

    def _do_scroll_event(self, _, e: Gdk.EventScroll):
        # Zoom in or out
        if e.direction == Gdk.ScrollDirection.UP or e.direction == Gdk.ScrollDirection.DOWN:
            x_to_use = self.actual_mouse_pos["x"]
            dt = self.timeline_canvas.pixel_to_datetime(x_to_use)
            zoom_in = e.direction == Gdk.ScrollDirection.UP
            self.timeline_canvas.zoom(zoom_in, dt)
        # Move right or left
        elif e.direction == Gdk.ScrollDirection.RIGHT or e.direction == Gdk.ScrollDirection.LEFT:
            move_right = e.direction == Gdk.ScrollDirection.RIGHT
            self.timeline_canvas.move(move_right)

    def _do_button_release(self, *_):
        self.timeline_canvas.do_button_release()

    def _do_button_press(self, _, e: Gdk.EventButton):
        self.timeline_canvas.do_button_press(e, self.current_moused_datetime)

    def _do_draw(self, _, cr: cairo.Context):
        height = self.get_allocated_height()
        width = self.get_allocated_width()
        timeline_canvas = self.timeline_canvas
        timeline_x = timeline_canvas.datetime_to_pixel(self.current_moused_datetime, width)

        # Show a guiding line under the mouse
        cr.set_source_rgb(0.5, 0.5, 0.5)
        cr.new_path()
        cr.move_to(timeline_x, 0)
        cr.line_to(timeline_x, height)
        cr.stroke()

        # Get the activity value under the mouse
        is_active = None
        mouse_x = self.actual_mouse_pos["x"]
        for ae in timeline_canvas.visible_activity_entries:
            if ae.start_x <= mouse_x <= ae.stop_x:
                is_active = ae.entry.active

        # Tooltip information setup
        dt = timeline_canvas.pixel_to_datetime(mouse_x)
        time_texts = [datetime_helper.to_time_str(dt)]
        desc_texts = []

        # See if we have an entry below the cursor. Use its information for the tooltip.
        mouse_y = self.actual_mouse_pos["y"]
        if timeline_canvas.le_start_y <= mouse_y <= timeline_canvas.le_end_y:
            for le in timeline_canvas.visible_logged_entries:
                if le.start_x <= mouse_x <= le.stop_x:
                    if timeline_canvas.current_tagged_entry is None:
                        time_details = datetime_helper.to_time_text(le.entry.start, le.entry.stop, le.entry.duration)
                        time_texts.append(time_details)
                    desc_texts.append(le.entry.application_window.application.name)
                    desc_texts.append(le.entry.application_window.title)

                    cr.set_source_rgba(0.7, 0.7, 0.7, 0.2)
                    cr.rectangle(le.start_x, timeline_canvas.le_start_y,
                                 le.stop_x - le.start_x, timeline_canvas.timeline_height)
                    cr.fill()
                    break
        elif timeline_canvas.te_start_y <= mouse_y <= timeline_canvas.te_end_y:
            for te in timeline_canvas.visible_tagged_entries:
                if te.start_x <= mouse_x <= te.stop_x:
                    time_details = datetime_helper.to_time_text(te.entry.start, te.entry.stop, te.entry.duration)
                    time_texts.append(time_details)
                    desc_texts.append(te.entry.category.name)

                    cr.set_source_rgba(0.7, 0.7, 0.7, 0.2)
                    cr.rectangle(te.start_x, timeline_canvas.te_start_y,
                                 te.stop_x - te.start_x, timeline_canvas.timeline_height)
                    cr.fill()

        # Show the tooltip
        self._show_details_tooltip(mouse_x, mouse_y, width, height, cr, time_texts, desc_texts, is_active)

    def _on_motion_notify(self, _, e: Gdk.EventMotion):
        stop_date = self.timeline_canvas.pixel_to_datetime(e.x)
        next_moused_datetime = stop_date

        if self.timeline_canvas.current_tagged_entry is not None:
            datetime_used = self.timeline_canvas._set_tagged_entry_stop_date(stop_date,
                                                                             self.timeline_canvas.current_tagged_entry,
                                                                             self.timeline_canvas.tagged_entries)
            if datetime_used is not None:
                next_moused_datetime = datetime_used
        else:
            for t in self.timeline_canvas.visible_tagged_entries:
                if e.x < t.start_x:
                    break
                elif e.x <= t.stop_x:
                    start_delta = e.x - t.start_x
                    stop_delta = t.stop_x - e.x

                    next_moused_datetime = t.entry.start if start_delta < stop_delta else t.entry.stop
                    break

        self.current_moused_datetime = next_moused_datetime
        self.actual_mouse_pos["x"], self.actual_mouse_pos["y"] = e.x, e.y

        self.queue_draw()

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
