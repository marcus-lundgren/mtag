import datetime
from entity.application_window import ApplicationWindow


class LoggedEntry:
    def __init__(self, start: datetime, stop: datetime, application_window: ApplicationWindow, db_id: int = None):
        self.db_id = db_id
        self.start = start
        self.stop = stop
        self.application_window = application_window
        self.duration = stop - start
