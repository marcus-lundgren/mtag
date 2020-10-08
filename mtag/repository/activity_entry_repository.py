import sqlite3
import datetime
from mtag.helper import datetime_helper
from mtag.entity import ActivityEntry


class ActivityEntryRepository:
    @staticmethod
    def insert(conn: sqlite3.Connection, activity_entry: ActivityEntry):
        conn.execute("INSERT INTO activity_entry(ae_start, ae_last_update, ae_active)"
                     " VALUES (:start, :last_update, :active)",
                     {"start": datetime_helper.datetime_to_timestamp(activity_entry.start),
                      "last_update": datetime_helper.datetime_to_timestamp(activity_entry.stop),
                      "active": 1 if activity_entry.active else 0})
        conn.commit()

    def get_latest_entry(self, conn: sqlite3.Connection):
        cursor = conn.execute(
                "SELECT * FROM activity_entry ORDER BY ae_last_update DESC")
        db_ae = cursor.fetchone()
        if db_ae is None:
            return None

        return self._from_dbo(db_ae=db_ae)

    def get_all_by_date(self, conn: sqlite3.Connection, date: datetime.datetime):
        from_datetime = datetime.datetime(year=date.year, month=date.month, day=date.day)
        to_datetime = from_datetime + datetime.timedelta(days=1)
        cursor = conn.execute("SELECT * FROM activity_entry WHERE"
                              " (:from_date <= ae_last_update AND ae_last_update < :to_date)"
                              " OR"
                              " (:from_date <= ae_start AND ae_start < :to_date)"
                              " ORDER BY ae_start ASC",
                              {"from_date": datetime_helper.datetime_to_timestamp(from_datetime),
                               "to_date": datetime_helper.datetime_to_timestamp(to_datetime)})
        db_activity_entries = cursor.fetchall()

        activity_entries = [self._from_dbo(db_ae=db_ae) for db_ae in db_activity_entries]
        return activity_entries

    def _from_dbo(self, db_ae: dict):
        return ActivityEntry(db_id=db_ae["ae_id"],
                             start=datetime_helper.timestamp_to_datetime(db_ae["ae_start"]),
                             stop=datetime_helper.timestamp_to_datetime(db_ae["ae_last_update"]),
                             active=db_ae["ae_active"] == 1)
