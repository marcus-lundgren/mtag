import sqlite3
import datetime
from entity import TaggedEntry
from repository.category_repository import CategoryRepository


class TaggedEntryRepository:
    def __init__(self):
        self.category_repository = CategoryRepository()

    def insert(self, conn: sqlite3.Connection, tagged_entry: TaggedEntry):
        conn.execute("INSERT INTO tagged_entry (te_category_id, te_start, te_end)"
                     " VALUES (:category_id, :start, :end)",
                     {"category_id": tagged_entry.category.db_id,
                      "start": tagged_entry.start,
                      "end": tagged_entry.stop})
        conn.commit()

    def get_all_by_date(self, conn: sqlite3.Connection, date: datetime.datetime):
        date_string = date.strftime("%Y-%m-%d")
        from_datetime = datetime.datetime.fromisoformat(f"{date_string} 00:00:00")
        to_datetime = from_datetime + datetime.timedelta(days=1)
        cursor = conn.execute("SELECT * FROM tagged_entry WHERE"
                              " (:from_date <= te_start AND te_start < :to_date)"
                              " OR"
                              " (:from_date <= te_end AND te_end < :to_date)",
                              {"from_date": from_datetime, "to_date": to_datetime})
        db_tagged_entries = cursor.fetchall()

        tagged_entries = []
        for db_te in db_tagged_entries:
            le = self._from_dbo(conn=conn, db_te=db_te)
            tagged_entries.append(le)

        return tagged_entries

    def total_time_by_category(self, conn: sqlite3.Connection, category_name: str):
        cursor = conn.execute("SELECT SUM(strftime('%s', te_end) - strftime('%s', te_start)) AS total_time"
                              " FROM tagged_entry"
                              " INNER JOIN category ON tagged_entry.te_category_id == category.c_id"
                              " WHERE c_name=:c_name",
                              { "c_name": category_name })
        total_seconds = cursor.fetchone()
        return total_seconds["total_time"]

    def _from_dbo(self, conn: sqlite3.Connection, db_te: dict):
        category = self.category_repository.get(conn=conn, db_id=db_te["te_category_id"])
        return TaggedEntry(start=db_te["te_start"], stop=db_te["te_end"], category=category, db_id=db_te["te_id"])
