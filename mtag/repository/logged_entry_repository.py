import sqlite3
import datetime
from typing import Dict, List, Optional

from mtag.helper import datetime_helper
from mtag.entity import LoggedEntry, ApplicationWindow
from mtag.repository import ApplicationWindowRepository


class LoggedEntryRepository:
    def __init__(self):
        self.application_window_repository = ApplicationWindowRepository()
        self.aw_cache = {}

    @staticmethod
    def insert(conn: sqlite3.Connection, logged_entry: LoggedEntry) -> None:
        conn.execute("INSERT INTO logged_entry(le_application_window_id, le_start, le_last_update)"
                     " VALUES (:application_window_id, :start, :last_update)",
                     {"application_window_id": logged_entry.application_window.db_id,
                      "start": datetime_helper.datetime_to_timestamp(logged_entry.start),
                      "last_update": datetime_helper.datetime_to_timestamp(logged_entry.stop)})
        conn.commit()

    def get_latest_entry(self, conn: sqlite3.Connection) -> Optional[LoggedEntry]:
        cursor = conn.execute(
                "SELECT * FROM logged_entry ORDER BY le_last_update DESC")
        db_le = cursor.fetchone()
        if db_le is None:
            return None

        return self._from_dbo(conn=conn, db_le=db_le)

    def get_all_by_date(self, conn: sqlite3.Connection, date: datetime.datetime) -> List[LoggedEntry]:
        from_datetime = datetime.datetime(year=date.year, month=date.month, day=date.day)
        to_datetime = from_datetime + datetime.timedelta(days=1)
        cursor = conn.execute("SELECT * FROM logged_entry WHERE"
                              " (:from_date <= le_last_update AND le_last_update < :to_date)"
                              " OR"
                              " (:from_date <= le_start AND le_start < :to_date)"
                              " ORDER BY le_start ASC",
                              {"from_date": datetime_helper.datetime_to_timestamp(from_datetime),
                               "to_date": datetime_helper.datetime_to_timestamp(to_datetime)})
        db_logged_entries = cursor.fetchall()

        return [self._from_dbo(conn=conn, db_le=db_le) for db_le in db_logged_entries]

    def _from_dbo(self, conn: sqlite3.Connection, db_le: Dict) -> LoggedEntry:
        application_window = self._get_application_window(conn, db_le["le_application_window_id"])

        return LoggedEntry(start=datetime_helper.timestamp_to_datetime(db_le["le_start"]),
                           stop=datetime_helper.timestamp_to_datetime(db_le["le_last_update"]),
                           application_window=application_window, db_id=db_le["le_id"])

    def _get_application_window(self, conn: sqlite3.Connection, aw_id: int) -> ApplicationWindow:
        if aw_id in self.aw_cache:
            return self.aw_cache[aw_id]

        application_window = self.application_window_repository.get(conn, aw_id)
        self.aw_cache[aw_id] = application_window
        return application_window
