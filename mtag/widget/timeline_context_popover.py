from mtag.entity import TaggedEntry

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject


class TimelineContextPopover(Gtk.Popover):
    @GObject.Signal(name="tagged-entry-delete-event",
                    flags=GObject.SignalFlags.RUN_LAST,
                    return_type=GObject.TYPE_BOOLEAN,
                    arg_types=[object])
    def tagged_entry_delete_event(self, *args):
        pass

    @GObject.Signal(name="tagged-entry-edit-category-event",
                    flags=GObject.SignalFlags.RUN_LAST,
                    return_type=GObject.TYPE_BOOLEAN,
                    arg_types=[object])
    def tagged_entry_edit_category_event(self, *args):
        pass

    def __init__(self, relative_to: Gtk.Widget):
        super().__init__()
        self.set_relative_to(relative_to=relative_to)
        self.set_modal(True)
        self.set_position(Gtk.PositionType.BOTTOM)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        button = Gtk.Button(label="Delete")
        button.connect("clicked", self._do_delete_button_clicked)
        button.show()
        box.pack_start(button, expand=True, fill=True, padding=0)

        button = Gtk.Button(label="Edit category")
        button.connect("clicked", self._do_edit_category_button_clicked)
        button.show()
        box.pack_end(button, expand=True, fill=True, padding=0)

        box.show()
        self.add(box)

        self.pointing_to_rectangle = Gdk.Rectangle()
        self.pointing_to_rectangle.x = 1
        self.pointing_to_rectangle.y = 1
        self.pointing_to_rectangle.width = 1
        self.pointing_to_rectangle.height = 1

        self.current_tagged_entry = None

    def _do_delete_button_clicked(self, w):
        self.popdown()
        self.emit("tagged-entry-delete-event", self.current_tagged_entry)

    def _do_edit_category_button_clicked(self, w):
        self.popdown()
        self.emit("tagged-entry-edit-category-event", self.current_tagged_entry)

    def popup_at_coordinate(self, x: float, y: float, te: TaggedEntry):
        self.current_tagged_entry = te
        self._set_pointing_to_coordinate(x, y)
        self.popup()

    def _set_pointing_to_coordinate(self, x: float, y: float):
        self.pointing_to_rectangle.x = x
        self.pointing_to_rectangle.y = y
        self.set_pointing_to(self.pointing_to_rectangle)
