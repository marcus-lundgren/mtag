from mtag.widget import MTagWindow
import gi
from gi.repository import Gtk


def start_mtag():
    _ = MTagWindow()
    Gtk.main()
