from entity.application_path import ApplicationPath

class Application:
    def __init__(self, name: str, application_path: ApplicationPath, db_id: int):
        self.db_id = db_id
        self.application_path = application_path
        self.name = name
