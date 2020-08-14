import sqlite3
from entity import LoggedEntry
from repository.application_repository import ApplicationRepository


class LoggedEntryRepository:
    def __init__(self):
        self.application_repository = ApplicationRepository()

    @staticmethod
    def insert(conn: sqlite3.Connection, logged_entry: LoggedEntry):
        conn.execute("INSERT INTO logged_entry(le_application_id, le_title, le_start, le_last_update)"
                     " VALUES (:application_id, :title, :start, :last_update)",
                     {"application_id": logged_entry.application.db_id, "title": logged_entry.title,
                      "start": logged_entry.start, "last_update": logged_entry.stop})
        conn.commit()

    def get_latest_entry(self, conn: sqlite3.Connection):
        cursor = conn.execute(
                "SELECT * FROM logged_entry ORDER BY le_last_update DESC")
        db_le = cursor.fetchone()
        if db_le is None:
            return None

        return self._from_dbo(conn=conn, db_le=db_le)

    def get_all(self, conn: sqlite3.Connection):
        cursor = conn.execute("SELECT * FROM logged_entry")
        db_logged_entries = cursor.fetchall()

        logged_entries = []
        for db_le in db_logged_entries:
            le = self._from_dbo(conn=conn, db_le=db_le)
            logged_entries.append(le)

        return logged_entries

    def _from_dbo(self, conn: sqlite3.Connection, db_le: dict):
        application = self.application_repository.get(conn, db_le["le_application_id"])
        return LoggedEntry(start=db_le["le_start"], stop=db_le["le_last_update"], application=application,
                           title=db_le["le_title"], db_id=db_le["le_id"])
