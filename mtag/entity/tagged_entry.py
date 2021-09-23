import datetime
from typing import Optional
from mtag.entity import Category


class TaggedEntry:
    def __init__(self, start: datetime, stop: datetime, category: Optional[Category], db_id: int = None):
        self.db_id = db_id
        self.start = start
        self._stop = stop
        self.initial_position = self.start
        self.category = category

    @property
    def duration(self):
        return self._stop - self.start

    @property
    def stop(self):
        return self._stop

    @stop.setter
    def stop(self, value):
        if value < self.initial_position:
            self._stop = self.initial_position
            self.start = value
        else:
            self.start = self.initial_position
            self._stop = value

    def contains_datetime(self, d: datetime):
        return self.start <= d <= self._stop
