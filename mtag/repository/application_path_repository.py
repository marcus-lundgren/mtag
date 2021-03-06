import sqlite3
from typing import Optional

from mtag.entity import ApplicationPath


class ApplicationPathRepository:
    @staticmethod
    def insert(conn: sqlite3.Connection, path: str) -> int:
        cursor = conn.execute("INSERT INTO application_path(ap_path) VALUES (:path)", {"path": path})
        conn.commit()
        return cursor.lastrowid

    @staticmethod
    def get_by_path(conn: sqlite3.Connection, path: str) -> Optional[ApplicationPath]:
        cursor = conn.execute("SELECT * FROM application_path WHERE ap_path=:path", {"path": path})
        dbo = cursor.fetchone()
        if dbo is None:
            return None

        return ApplicationPath(path=dbo["ap_path"], db_id=dbo["ap_id"])

    @staticmethod
    def get(conn: sqlite3.Connection, db_id: int) -> Optional[ApplicationPath]:
        cursor = conn.execute("SELECT * FROM application_path WHERE ap_id=:db_id", {"db_id": db_id})
        dbo = cursor.fetchone()
        if dbo is None:
            return None

        return ApplicationPath(path=dbo["ap_path"], db_id=db_id)
