import datetime
from entity.category import Category


class TaggedEntry():
    def __init__(self, start: datetime, stop: datetime, category: Category, db_id: int = None):
        self.db_id = db_id
        self.start = start
        self._stop = stop
        self._category = category

    @property
    def category(self):
        return self._category

    @property
    def stop(self):
        return self._stop

    @stop.setter
    def stop(self, value):
        self._stop = value
