import datetime
import logging
from typing import Optional

from mtag.entity import LoggedEntry, Application, ApplicationWindow, ApplicationPath, ActivityEntry
from mtag.helper import database_helper, datetime_helper, configuration_helper
from mtag.repository import ApplicationRepository, ApplicationPathRepository
from mtag.repository import LoggedEntryRepository, ApplicationWindowRepository
from mtag.repository import ActivityEntryRepository


def register(window_title: Optional[str], application_name: Optional[str],
             application_path: Optional[str], idle_period: Optional[int],
             locked_state: bool = False) -> None:
    configuration = configuration_helper.get_configuration()

    window_title_to_use = window_title if window_title is not None else "N/A"
    application_name_to_use = application_name if application_name is not None else "N/A"
    application_path_to_use = application_path if application_path is not None else "N/A"
    application_path_to_use = application_path_to_use if configuration.log_application_path else "N/A"
    idle_period_to_use = idle_period if idle_period is not None else 0

    logging.info(f"Idle period in seconds: {idle_period_to_use}")
    logging.info(application_path_to_use)
    logging.info(f"{application_name_to_use} -> {window_title_to_use}")

    # Application path
    application_path = insert_if_needed_and_get_application_path(application_path=application_path_to_use)

    # Application
    application = insert_if_needed_and_get_application(application_name=application_name_to_use,
                                                       application_path=application_path)

    # Application window
    application_window = insert_if_needed_and_get_application_window(application=application,
                                                                     window_title=window_title_to_use)

    datetime_now = datetime.datetime.now()

    # Logged entry
    register_logged_entry(application_window=application_window, datetime_now=datetime_now)

    # Activity entry
    register_activity_entry(idle_period=idle_period_to_use, locked_state=locked_state, datetime_now=datetime_now)


def register_activity_entry(idle_period: int, locked_state: bool, datetime_now: datetime.datetime):
    configuration = configuration_helper.get_configuration()
    activity_entry_repository = ActivityEntryRepository()
    was_active = not locked_state and idle_period < configuration.inactive_after_idle_seconds

    with database_helper.create_connection() as db_connection:
        last_activity_entry = activity_entry_repository.get_latest_entry(conn=db_connection)
        if last_activity_entry is None:
            logging.info("No existing activity entry, creating a new one")
            new_update = datetime_now + datetime.timedelta(seconds=1)
            activity_entry = ActivityEntry(start=datetime_now, stop=new_update, active=was_active)
            activity_entry_repository.insert(conn=db_connection, activity_entry=activity_entry)
        else:
            max_delta_seconds = configuration.seconds_before_new_entry
            max_delta_period = datetime.timedelta(seconds=max_delta_seconds)

            old_end = last_activity_entry.stop
            if max_delta_period < datetime_now - old_end:
                logging.info("Too long since last update. Create a new entry.")

                new_update = datetime_now + datetime.timedelta(seconds=1)
                activity_entry = ActivityEntry(start=datetime_now, stop=new_update, active=was_active)
                activity_entry_repository.insert(db_connection, activity_entry)
            elif last_activity_entry.active == was_active:
                logging.info("Still same activity level. Update existing entry")

                db_connection.execute("UPDATE activity_entry SET ae_last_update=:new_update WHERE ae_id=:id",
                                      {"id": last_activity_entry.db_id,
                                       "new_update": datetime_helper.datetime_to_timestamp(datetime_now)})
            else:
                logging.info("Not the same activity level. Insert new activity entry")

                activity_entry = ActivityEntry(start=last_activity_entry.stop, stop=datetime_now, active=was_active)
                activity_entry_repository.insert(db_connection, activity_entry)

        db_connection.commit()


def register_logged_entry(application_window: ApplicationWindow, datetime_now: datetime.datetime):
    logged_entry_repository = LoggedEntryRepository()

    with database_helper.create_connection() as db_connection:
        last_logged_entry = logged_entry_repository.get_latest_entry(conn=db_connection)
        if last_logged_entry is None:
            logging.info("No existing logged entry, creating a new one")
            new_update = datetime_now + datetime.timedelta(seconds=1)
            logged_entry = LoggedEntry(start=datetime_now,
                                       stop=new_update,
                                       application_window=application_window)
            logged_entry_repository.insert(conn=db_connection, logged_entry=logged_entry)
        else:
            configuration = configuration_helper.get_configuration()
            max_delta_seconds = configuration.seconds_before_new_entry
            max_delta_period = datetime.timedelta(seconds=max_delta_seconds)

            old_end = last_logged_entry.stop
            if max_delta_period < datetime_now - old_end:
                logging.info("Too long since last update. Create a new entry.")

                new_update = datetime_now + datetime.timedelta(seconds=1)
                logged_entry = LoggedEntry(start=datetime_now, stop=new_update, application_window=application_window)
                logged_entry_repository.insert(db_connection, logged_entry)
            elif last_logged_entry.application_window.db_id == application_window.db_id:
                logging.info("Still same window. Update existing logged entry")

                db_connection.execute("UPDATE logged_entry SET le_last_update=:new_update WHERE le_id=:id",
                                      {"id": last_logged_entry.db_id,
                                       "new_update": datetime_helper.datetime_to_timestamp(datetime_now)})
            else:
                logging.info("Not the same window. Insert new logged entry")

                logged_entry = LoggedEntry(start=last_logged_entry.stop, stop=datetime_now,
                                           application_window=application_window)
                logged_entry_repository.insert(db_connection, logged_entry)

        db_connection.commit()


def insert_if_needed_and_get_application_window(application: Application, window_title: str) -> ApplicationWindow:
    with database_helper.create_connection() as db_connection:
        application_window_repository = ApplicationWindowRepository()
        application_window = application_window_repository.get_by_title_and_application_id(conn=db_connection,
                                                                                           title=window_title,
                                                                                           application_id=application.db_id)

        # We couldn't find an existing entry in the database. Insert a new one.
        if application_window is None:
            logging.info("Adding new application window")
            application_window = ApplicationWindow(title=window_title, application=application)
            db_id = application_window_repository.insert(conn=db_connection, application_window=application_window)
            application_window.db_id = db_id

    logging.debug(f"application_window_id = {application_window.db_id}")
    return application_window


def insert_if_needed_and_get_application(application_name: str, application_path: ApplicationPath) -> Application:
    with database_helper.create_connection() as db_connection:
        application_repository = ApplicationRepository()
        application = application_repository.get_by_name_and_path_id(conn=db_connection,
                                                                     name=application_name,
                                                                     path_id=application_path.db_id)

        # We couldn't find an existing entry in the database. Insert a new one.
        if application is None:
            logging.info("Adding new application")
            application_id = application_repository.insert(conn=db_connection,
                                                           name=application_name,
                                                           application_path=application_path)
            application = application_repository.get(db_connection, application_id)

    logging.debug(f"application_id = {application.db_id}")
    return application


def insert_if_needed_and_get_application_path(application_path: str) -> ApplicationPath:
    with database_helper.create_connection() as db_connection:
        application_path_repository = ApplicationPathRepository()
        ap = application_path_repository.get_by_path(conn=db_connection, path=str(application_path))

        # We couldn't find an existing entry in the database. Insert a new one.
        if ap is None:
            logging.info("Adding new application path")
            application_path_id = application_path_repository.insert(db_connection, str(application_path))
        else:
            application_path_id = ap.db_id
        application_path = application_path_repository.get(conn=db_connection, db_id=application_path_id)

    return application_path
