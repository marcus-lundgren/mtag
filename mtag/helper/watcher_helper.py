import datetime
import sqlite3
import logging

from mtag.entity import LoggedEntry, Application, ApplicationWindow
from mtag.helper import database_helper, datetime_helper, configuration_helper
from mtag.repository import LoggedEntryRepository, ApplicationWindowRepository
from mtag.repository import ApplicationRepository, ApplicationPathRepository


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
        logging.info("Adding new application window")
        application_window = ApplicationWindow(title=window_title, application=application)
        db_id = application_window_repository.insert(conn=db_connection, application_window=application_window)
        application_window.db_id = db_id

    logging.debug(f"application_window_id = {application_window.db_id}")

    # Logged entry
    logged_entry_repository = LoggedEntryRepository()
    last_logged_entry = logged_entry_repository.get_latest_entry(db_connection)
    datetime_now = datetime.datetime.now()
    configuration = configuration_helper.get_configuration()
    if last_logged_entry is None:
        logging.info("No existing logged entry, creating a new one")
        new_update = datetime_now + datetime.timedelta(seconds=1)
        logged_entry = LoggedEntry(start=datetime_now,
                                   stop=new_update,
                                   application_window=application_window)
        logged_entry_repository.insert(db_connection, logged_entry)
    else:
        seconds = configuration[configuration_helper.WATCHER_MAX_DELTA_SECONDS_BEFORE_NEW]
        max_delta_period = datetime.timedelta(seconds=seconds)

        logging.debug("Last logged stop:", last_logged_entry.stop)
        old_end = last_logged_entry.stop
        if max_delta_period < datetime_now - old_end:
            logging.info("Too long since last update. Create a new entry.")
            logged_entry = LoggedEntry(start=datetime_now, stop=datetime_now, application_window=application_window)
            logged_entry_repository.insert(db_connection, logged_entry)
        elif last_logged_entry.application_window.db_id == application_window.db_id:
            logging.info("Still same window. Update existing logged entry")
            db_cursor.execute("UPDATE logged_entry SET le_last_update=:new_update WHERE le_id=:id",
                              {"id": last_logged_entry.db_id,
                               "new_update": datetime_helper.datetime_to_timestamp(datetime_now)})
        else:
            logging.info("Not the same window. Insert new logged entry")
            logged_entry = LoggedEntry(start=last_logged_entry.stop, stop=datetime_now,
                                       application_window=application_window)
            logged_entry_repository.insert(db_connection, logged_entry)

    db_connection.commit()
    db_connection.close()


def get_and_create_if_needed_application(conn: sqlite3.Connection, application_name: str, application_path: str) -> Application:
    # Application path
    application_path_repository = ApplicationPathRepository()
    ap = application_path_repository.get_by_path(conn=conn, path=str(application_path))
    if ap is None:
        logging.info("Adding new application path")
        application_path_id = application_path_repository.insert(conn, str(application_path))
    else:
        application_path_id = ap.db_id
    application_path = application_path_repository.get(conn=conn, db_id=application_path_id)

    # Application
    application_repository = ApplicationRepository()
    application = application_repository.get_by_name_and_path_id(conn, application_name, application_path.db_id)
    if application is None:
        logging.info("Adding new application")
        application_id = application_repository.insert(conn=conn,
                                                       name=application_name,
                                                       application_path=application_path)
        application = application_repository.get(conn, application_id)

    logging.debug(f"application_id = {application.db_id}")
    return application
