from entity import Application


class ApplicationWindow:
    def __init__(self, title: str, application: Application, db_id: int = None):
        self.title = title
        self.application = application
        self.db_id = db_id
