import sqlite3
import datetime
from typing import Dict, List

from mtag.helper import datetime_helper
from mtag.entity import TaggedEntry, Category
from mtag.repository import CategoryRepository


class TaggedEntryRepository:
    def __init__(self):
        self.category_repository = CategoryRepository()
        self.category_cache = {}

    def insert(self, conn: sqlite3.Connection, tagged_entry: TaggedEntry) -> None:
        cursor = conn.execute("SELECT te_id, te_start"
                              " FROM tagged_entry"
                              " WHERE te_end==:new_te_start"
                              " AND te_category_id==:new_te_category_id",
                              {"new_te_start": datetime_helper.datetime_to_timestamp(tagged_entry.start),
                               "new_te_category_id": tagged_entry.category.db_id})
        te_to_the_left_dbo = cursor.fetchone()
        cursor.execute("SELECT te_id, te_end"
                       " FROM tagged_entry"
                       " WHERE te_start==:new_te_end"
                       " AND te_category_id==:new_te_category_id",
                       {"new_te_end": datetime_helper.datetime_to_timestamp(tagged_entry.stop),
                        "new_te_category_id": tagged_entry.category.db_id})
        te_to_the_right_dbo = cursor.fetchone()

        # We have neighbours to the left and right. Update the one to the left
        # and delete the one to the right.
        if te_to_the_left_dbo is not None and te_to_the_right_dbo is not None:
            cursor.execute("DELETE FROM tagged_entry WHERE te_id=:te_right_id",
                           {"te_right_id": te_to_the_right_dbo["te_id"]})
            cursor.execute("UPDATE tagged_entry SET te_end=:right_te_end WHERE te_id==:te_left_id",
                           {"right_te_end": te_to_the_right_dbo["te_end"],
                            "te_left_id": te_to_the_left_dbo["te_id"]})
        # Update the entry to the left instead of creating a new one
        elif te_to_the_left_dbo is not None:
            cursor.execute("UPDATE tagged_entry SET te_end=:new_te_end WHERE te_id==:te_left_id",
                           {"new_te_end": datetime_helper.datetime_to_timestamp(tagged_entry.stop),
                            "te_left_id": te_to_the_left_dbo["te_id"]})
        # Update the entry to the right instead of creating a new one
        elif te_to_the_right_dbo is not None:
            cursor.execute("UPDATE tagged_entry SET te_start=:new_te_start WHERE te_id==:te_right_id",
                           {"new_te_start": datetime_helper.datetime_to_timestamp(tagged_entry.start),
                            "te_right_id": te_to_the_right_dbo["te_id"]})
        # No relevant neighbour. Create a new entry
        else:
            cursor.execute("INSERT INTO tagged_entry (te_category_id, te_start, te_end)"
                           " VALUES (:category_id, :start, :end)",
                           {"category_id": tagged_entry.category.db_id,
                            "start": datetime_helper.datetime_to_timestamp(tagged_entry.start),
                            "end": datetime_helper.datetime_to_timestamp(tagged_entry.stop)})

        conn.commit()

    def delete(self, conn: sqlite3.Connection, db_id: int) -> None:
        conn.execute("DELETE FROM tagged_entry WHERE te_id=:db_id", {"db_id": db_id})
        conn.commit()

    def get_all_by_date(self, conn: sqlite3.Connection, date: datetime.datetime) -> List[TaggedEntry]:
        from_datetime = datetime.datetime(year=date.year, month=date.month, day=date.day)
        to_datetime = from_datetime + datetime.timedelta(days=1)
        cursor = conn.execute("SELECT * FROM tagged_entry WHERE"
                              " (:from_date <= te_start AND te_start < :to_date)"
                              " OR"
                              " (:from_date <= te_end AND te_end < :to_date)"
                              " ORDER BY te_start ASC",
                              {"from_date": datetime_helper.datetime_to_timestamp(from_datetime),
                               "to_date": datetime_helper.datetime_to_timestamp(to_datetime)})
        db_tagged_entries = cursor.fetchall()

        return [self._from_dbo(conn=conn, db_te=db_te) for db_te in db_tagged_entries]

    def total_time_by_category(self, conn: sqlite3.Connection, category_name: str) -> int:
        cursor = conn.execute("SELECT SUM(te_end - te_start) AS total_time"
                              " FROM tagged_entry"
                              " INNER JOIN category ON tagged_entry.te_category_id == category.c_id"
                              " WHERE c_name=:c_name",
                              {"c_name": category_name})
        row = cursor.fetchone()
        total_seconds = row["total_time"]
        return 0 if total_seconds is None else total_seconds

    def _from_dbo(self, conn: sqlite3.Connection, db_te: dict) -> TaggedEntry:
        category = self._get_category(conn=conn, c_id=db_te["te_category_id"])
        return TaggedEntry(start=datetime_helper.timestamp_to_datetime(db_te["te_start"]),
                           stop=datetime_helper.timestamp_to_datetime(db_te["te_end"]),
                           category=category,
                           db_id=db_te["te_id"])

    def _get_category(self, conn: sqlite3.Connection, c_id: int) -> Category:
        if c_id in self.category_cache:
            return self.category_cache[c_id]

        category = self.category_repository.get(conn=conn, db_id=c_id)
        self.category_cache[c_id] = category
        return category
