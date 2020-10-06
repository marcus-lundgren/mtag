import datetime
from typing import Optional


class ActivityEntry:
    def __init__(self, active: bool, start: datetime.datetime, stop: datetime.datetime, db_id: Optional[int] = None):
        self.db_id = db_id
        self.active = active
        self.start = start
        self.stop = stop
        self.duration = stop - start
