import datetime
import sqlite3

from mtag.entity import LoggedEntry
from mtag.entity.application_window import ApplicationWindow
from mtag.helper import database_helper, datetime_helper
from mtag.repository.application_path_repository import ApplicationPathRepository
from mtag.repository.application_repository import ApplicationRepository
from mtag.repository.application_window_repository import ApplicationWindowRepository
from mtag.repository.logged_entry_repository import LoggedEntryRepository


def register(window_title: str, application_name: str, application_path: str) -> None:
    db_connection = database_helper.create_connection()
    db_cursor = db_connection.cursor()

    application_path_to_use = application_path if application_path is not None else "N/A"

    application = get_and_create_if_needed_application(conn=db_connection,
                                                       application_name=application_name,
                                                       application_path=application_path_to_use)

    # Application window
    application_window_repository = ApplicationWindowRepository()
    application_window = application_window_repository.get_by_title_and_application_id(conn=db_connection,
                                                                                       title=window_title,
                                                                                       application_id=application.db_id)
    if application_window is None:
        print("Adding new application window")
        application_window = ApplicationWindow(title=window_title, application=application)
        db_id = application_window_repository.insert(conn=db_connection, application_window=application_window)
        application_window.db_id = db_id

    print(f"application_window_id = {application_window.db_id}")

    # Logged entry
    logged_entry_repository = LoggedEntryRepository()
    last_logged_entry = logged_entry_repository.get_latest_entry(db_connection)
    datetime_now = datetime.datetime.now()
    if last_logged_entry is None:
        print("No existing logged entry, creating a new one")
        new_update = datetime_now + datetime.timedelta(seconds=1)
        logged_entry = LoggedEntry(start=datetime_now,
                                   stop=new_update,
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
                              {"id": last_logged_entry.db_id,
                               "new_update": datetime_helper.datetime_to_timestamp(datetime_now)})
        else:
            print("Not the same window. Insert new logged entry")
            logged_entry = LoggedEntry(start=last_logged_entry.stop, stop=datetime_now,
                                       application_window=application_window)
            logged_entry_repository.insert(db_connection, logged_entry)

    db_connection.commit()
    db_connection.close()


def get_and_create_if_needed_application(conn: sqlite3.Connection, application_name: str, application_path: str):
    # Application path
    application_path_repository = ApplicationPathRepository()
    ap = application_path_repository.get_by_path(conn=conn, path=str(application_path))
    if ap is None:
        print("Adding new application path")
        application_path_id = application_path_repository.insert(conn, str(application_path))
    else:
        application_path_id = ap.db_id
    application_path = application_path_repository.get(conn=conn, db_id=application_path_id)

    # Application
    application_repository = ApplicationRepository()
    application = application_repository.get_by_name_and_path_id(conn, application_name, application_path.db_id)
    if application is None:
        print("Adding new application")
        application_id = application_repository.insert(conn=conn,
                                                       name=application_name,
                                                       application_path=application_path)
        application = application_repository.get(conn, application_id)

    print(f"application_id = {application.db_id}")
    return application
