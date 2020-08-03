import gi
import sqlite3
import datetime
import subprocess

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
    exit(0)

application = active_window.get_application()
application_pid = application.get_pid()
application_name = active_window.get_class_group_name()

print(application_pid)
application_path = subprocess.run(["cat", f"/proc/{int(application_pid)}/cmdline"], stdout=subprocess.PIPE, universal_newlines=True).stdout
print(application_path)
print(f"{application_name} -> {active_window.get_name()}")

db_connection = sqlite3.connect("test.db")
db_connection.row_factory = sqlite3.Row
db_cursor = db_connection.cursor()

db_cursor.execute("SELECT id FROM application_path WHERE path=:path", {"path": str(application_path)})
application_path_id = db_cursor.fetchone()
if application_path_id is None:
    print("Adding new application path")
    db_cursor.execute("INSERT INTO application_path(path) VALUES (:path)", {"path": application_path})
    application_path_id = db_cursor.lastrowid
else:
    application_path_id = application_path_id["id"]

db_cursor.execute("SELECT id FROM application WHERE name=:name AND path_id=:path_id", {"name": application_name, "path_id": application_path_id})
application_id = db_cursor.fetchone()
if application_id is None:
    print("Adding new application")
    db_cursor.execute("INSERT INTO application(name, path_id) VALUES (:name, :path_id)", {"name": application_name, "path_id":application_path_id})
    application_id = db_cursor.lastrowid
else:
    application_id = application_id["id"]

print(f"application_id = {application_id}")

db_cursor.execute("SELECT * FROM logged_entry ORDER BY end DESC")
last_logged_entry = db_cursor.fetchone()
datetime_now = datetime.datetime.now()
if last_logged_entry is None:
    print("No existing logged entry, creating a new one")
    db_cursor.execute("INSERT INTO logged_entry(application_id, title, start, end) VALUES (:application_id, :title, :start, :end)", {"application_id": application_id, "title": active_window.get_name(), "start": datetime_now, "end": datetime_now})
else:
    max_delta_period = datetime.timedelta(seconds=10)
    print(last_logged_entry["end"])
    old_end = datetime.datetime.strptime(last_logged_entry["end"], "%Y-%m-%d %H:%M:%S.%f")
    if max_delta_period < datetime_now - old_end:
        print("Too long since last update. Create a new entry.")
        db_cursor.execute("INSERT INTO logged_entry(application_id, title, start, end) VALUES (:application_id, :title, :start, :end)", {"application_id": application_id, "title": active_window.get_name(), "start": last_logged_entry["end"], "end": datetime_now})
    elif last_logged_entry["application_id"] == application_id and last_logged_entry["title"] == active_window.get_name():
        print("Still same window. Update existing logged entry")
        db_cursor.execute("UPDATE logged_entry SET end=:new_end WHERE id=:id", {"id": last_logged_entry["id"], "new_end": datetime_now})
    else:
        print("Not the same window. Insert new logged entry")
        db_cursor.execute("INSERT INTO logged_entry(application_id, title, start, end) VALUES (:application_id, :title, :start, :end)", {"application_id": application_id, "title": active_window.get_name(), "start": last_logged_entry["end"], "end": datetime_now})

db_connection.commit()
db_connection.close()
