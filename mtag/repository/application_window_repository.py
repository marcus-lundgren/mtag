import sqlite3
from typing import Dict, Optional

from mtag.entity import ApplicationWindow, Application
from mtag.repository import ApplicationRepository


class ApplicationWindowRepository:
    def __init__(self):
        self.application_repository = ApplicationRepository()
        self.application_cache = {}

    def insert(self, conn: sqlite3.Connection, application_window: ApplicationWindow) -> int:
        cursor = conn.execute("INSERT INTO application_window(aw_application_id, aw_title)"
                              + " VALUES (:application_id, :title)",
                              {"application_id": application_window.application.db_id,
                               "title": application_window.title})
        conn.commit()
        return cursor.lastrowid

    def get(self, conn: sqlite3.Connection, db_id: int) -> Optional[ApplicationWindow]:
        cursor = conn.execute("SELECT * FROM application_window WHERE aw_id=:db_id",
                              {"db_id": db_id})
        db_aw = cursor.fetchone()
        if db_aw is None:
            return None

        return self._from_dbo(conn=conn, db_aw=db_aw)

    def get_by_title_and_application_id(self, conn: sqlite3.Connection, title: str, application_id: int) -> Optional[ApplicationWindow]:
        cursor = conn.execute("SELECT * FROM application_window"
                              " WHERE aw_title=:title AND aw_application_id=:application_id",
                              {"title": title, "application_id": application_id})
        db_aw = cursor.fetchone()
        if db_aw is None:
            return None

        return self._from_dbo(conn=conn, db_aw=db_aw)

    def _from_dbo(self, conn: sqlite3.Connection, db_aw: Dict) -> ApplicationWindow:
        application = self._get_application(conn=conn, application_id=db_aw["aw_application_id"])
        return ApplicationWindow(db_id=db_aw["aw_id"], application=application, title=db_aw["aw_title"])

    def _get_application(self, conn:sqlite3.Connection, application_id: int) -> Application:
        if application_id in self.application_cache:
            return self.application_cache[application_id]

        application = self.application_repository.get(conn=conn, db_id=application_id)
        self.application_cache[application_id] = application
        return application
