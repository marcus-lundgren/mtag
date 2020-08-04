import datetime
from entity.category import Category


class TaggedEntry():
    def __init__(self, start: datetime, stop: datetime, category: Category, db_id: int = None):
        self.db_id = db_id
        self.start = start
        self._stop = stop
        self.initial_position = self.start
        self._category = category

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        self._category = value

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
