import subprocess

from mtag.helper import watcher_helper

import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck


print("== STARTED ==")

# xprop_root_output = subprocess.run(["xprop", "-root"], stdout=subprocess.PIPE, universal_newlines=True).stdout
# print(xprop_root_output)
# window_id = None
# for line in xprop_root_output.splitlines():
#     print(line)
#     if line.startswith("_NET_ACTIVE_WINDOW"):
#         line_split = line.split(" ")
#         window_id = line_split[len(line_split) - 1]
#         print(f"Active window ID: {window_id}")
#         break
#
# if window_id is None:
#     exit(0)
#
# xprop_id_output = subprocess.run(["xprop", "-id", window_id], stdout=subprocess.PIPE, universal_newlines=True).stdout
# print(xprop_id_output)
#
# exit(0)

default_screen = Wnck.Screen.get_default()
default_screen.force_update()

active_window = default_screen.get_active_window()
if active_window is None:
    print("No active window.")
    exit(0)

application = active_window.get_application()
application_pid = application.get_pid()

application_name = active_window.get_class_group_name()

print(application_pid)
application_path = ""

active_window_title = active_window.get_name()
if application_pid != 0:
    application_path = subprocess.run(["cat", f"/proc/{int(application_pid)}/cmdline"],
                                      stdout=subprocess.PIPE, universal_newlines=True).stdout
    print(application_path)
    application_path = application_path.replace("\0", " ")
    application_path = application_path.strip()
    print(f"{application_name} -> {active_window_title}")

watcher_helper.register(window_title=active_window_title, application_name=application_name, application_path=application_path)
