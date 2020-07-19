import datetime
from entity.application import Application


class LoggedEntry():
    def __init__(self, start: datetime, stop: datetime, application: Application, title: str, db_id: int = None):
        self.db_id = db_id
        self.start = start
        self.stop = stop
        self.application = application
        self.title = title
