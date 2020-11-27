import sqlite3
from typing import Dict, Optional

from mtag.entity import Application, ApplicationPath
from mtag.repository import ApplicationPathRepository


class ApplicationRepository:
    def __init__(self):
        self.application_path_repository = ApplicationPathRepository()
        self.ap_cache = {}

    def insert(self, conn: sqlite3.Connection, name: str, application_path: ApplicationPath) -> int:
        cursor = conn.execute("INSERT INTO application(a_name, a_path_id) VALUES (:name, :path_id)",
                              {"name": name, "path_id": application_path.db_id})
        conn.commit()
        return cursor.lastrowid

    def get_by_name_and_path_id(self, conn: sqlite3.Connection, name: str, path_id: int) -> Optional[Application]:
        cursor = conn.execute("SELECT * FROM application WHERE a_name=:name AND a_path_id=:path_id",
                              {"name": name, "path_id": path_id})
        db_a = cursor.fetchone()
        if db_a is None:
            return None

        return self._from_dbo(conn, db_a)

    def get(self, conn: sqlite3.Connection, db_id: int) -> Optional[Application]:
        cursor = conn.execute("SELECT * FROM application WHERE a_id=:db_id", {"db_id": db_id})
        db_a = cursor.fetchone()
        if db_a is None:
            return None

        return self._from_dbo(conn, db_a)

    def _from_dbo(self, conn: sqlite3.Connection, db_a: Dict) -> Application:
        application_path = self._get_application_path(conn, db_a["a_path_id"])
        return Application(name=db_a["a_name"], application_path=application_path, db_id=db_a["a_id"])

    def _get_application_path(self, conn: sqlite3.Connection, application_path_id: int) -> ApplicationPath:
        if application_path_id in self.ap_cache:
            return self.ap_cache[application_path_id]

        application_path = self.application_path_repository.get(conn, application_path_id)
        self.ap_cache[application_path_id] = application_path
        return application_path
