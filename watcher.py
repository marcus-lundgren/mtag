import gi
import sqlite3

gi.require_version('Wnck', '3.0')

from gi.repository import Wnck

default_screen = Wnck.Screen.get_default()
default_screen.force_update()

active_window = default_screen.get_active_window()
if active_window is None:
    exit(0)

application = active_window.get_application()
print(f"{application.get_name()} -> {active_window.get_name()}")

db_connection = sqlite3.connect("test.db")
db_cursor = db_connection.cursor()

db_cursor.execute("SELECT id FROM application WHERE name=:name", {"name": application.get_name()})
application_id = db_cursor.fetchone()
if application_id is None:
    print("Adding new application")
    db_cursor.execute("INSERT INTO application(name) VALUES (:name)", {"name": application.get_name()})
    application_id = db_cursor.lastrowid
application_id = application_id[0]
print(f"application_id = {application_id}")

db_cursor.execute("SELECT * FROM logged_entry ORDER BY end DESC")
last_logged_entry = db_cursor.fetchone()
if last_logged_entry is None:
    print("No existing logged entry, creating a new one")
    import datetime
    datetime_now = datetime.datetime.now()
    db_cursor.execute("INSERT INTO logged_entry(application_id, title, start, end) VALUES (:application_id, :title, :start, :end)", {"application_id": application_id, "title": active_window.get_name(), "start": datetime_now, "end": datetime_now})
else:
    print(last_logged_entry)


db_connection.commit()
db_connection.close()