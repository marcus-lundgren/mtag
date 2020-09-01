import gi
import sqlite3
import datetime
import subprocess

from entity import LoggedEntry
from entity.application_window import ApplicationWindow
from helper import database_helper
from repository import application_repository
from repository.application_path_repository import ApplicationPathRepository
from repository.application_repository import ApplicationRepository
from repository.application_window_repository import ApplicationWindowRepository
from repository.logged_entry_repository import LoggedEntryRepository

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

db_connection = database_helper.create_connection()
db_cursor = db_connection.cursor()

# Application path
application_path_repository = ApplicationPathRepository()
application_path_id = None
ap = application_path_repository.get_by_path(conn=db_connection, path=str(application_path))
if ap is None:
    print("Adding new application path")
    application_path_id = application_path_repository.insert(db_connection, str(application_path))
else:
    application_path_id = ap.db_id

# Application
application_repository = ApplicationRepository()
application = application_repository.get_by_name_and_path_id(db_connection, application_name, application_path_id)
if application is None:
    print("Adding new application")
    db_cursor.execute("INSERT INTO application(a_name, a_path_id) VALUES (:name, :path_id)",
                      {"name": application_name, "path_id": application_path_id})
    application = application_repository.get(db_connection, db_cursor.lastrowid)

print(f"application_id = {application.db_id}")

# Application window
application_window_repository = ApplicationWindowRepository()
application_window = application_window_repository.get_by_title_and_application_id(conn=db_connection,
                                                                                   title=active_window_title,
                                                                                   application_id=application.db_id)
if application_window is None:
    print("Adding new application window")
    application_window = ApplicationWindow(title=active_window_title, application=application)
    db_id = application_window_repository.insert(conn=db_connection, application_window=application_window)
    application_window.db_id = db_id

# Logged entry
logged_entry_repository = LoggedEntryRepository()
last_logged_entry = logged_entry_repository.get_latest_entry(db_connection)
datetime_now = datetime.datetime.now()
if last_logged_entry is None:
    print("No existing logged entry, creating a new one")
    new_update = datetime_now + datetime.timedelta(seconds=1)
    logged_entry = LoggedEntry(start=datetime_now, stop=new_update,
                               application_window=application_window)
    logged_entry_repository.insert(db_connection, logged_entry)
else:
    max_delta_period = datetime.timedelta(seconds=10)
    print(last_logged_entry.stop)
    old_end = last_logged_entry.stop
    if max_delta_period < datetime_now - old_end:
        print("Too long since last update. Create a new entry.")
        logged_entry = LoggedEntry(start=datetime_now, stop=datetime_now, application_window=application_window)
        logged_entry_repository.insert(db_connection, logged_entry)
    elif last_logged_entry.application_window.db_id == application_window.db_id:
        print("Still same window. Update existing logged entry")
        db_cursor.execute("UPDATE logged_entry SET le_last_update=:new_update WHERE le_id=:id",
                          {"id": last_logged_entry.db_id, "new_update": datetime_now})
    else:
        print("Not the same window. Insert new logged entry")
        logged_entry = LoggedEntry(start=last_logged_entry.stop, stop=datetime_now,
                                   application_window=application_window)
        logged_entry_repository.insert(db_connection, logged_entry)

db_connection.commit()
db_connection.close()
