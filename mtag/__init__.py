from mtag.widget.mtag_window import MTagWindow
import gi
from gi.repository import Gtk

def start_mtag():
    _ = MTagWindow()
    Gtk.main()
