import sqlite3
from mtag.entity.application import Application
from mtag.repository.application_path_repository import ApplicationPathRepository


class ApplicationRepository:
    def __init__(self):
        self.application_path_repository = ApplicationPathRepository()

    def get_by_name_and_path_id(self, conn: sqlite3.Connection, name: str, path_id: int):
        cursor = conn.execute("SELECT * FROM application WHERE a_name=:name AND a_path_id=:path_id",
                              {"name": name, "path_id": path_id})
        db_a = cursor.fetchone()
        if db_a is None:
            return None

        return self._from_dbo(conn, db_a)

    def get(self, conn: sqlite3.Connection, db_id: int):
        cursor = conn.execute("SELECT * FROM application WHERE a_id=:db_id", {"db_id": db_id})
        db_a = cursor.fetchone()
        if db_a is None:
            return None

        return self._from_dbo(conn, db_a)

    def _from_dbo(self, conn: sqlite3.Connection, db_a: dict):
        application_path = self.application_path_repository.get(conn, db_a["a_path_id"])
        return Application(name=db_a["a_name"], application_path=application_path, db_id=db_a["a_id"])
