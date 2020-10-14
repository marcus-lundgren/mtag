from mtag.helper import color_helper


class Category:
    def __init__(self, name: str, db_id: int = None):
        self.db_id = db_id
        self._name = name

    @property
    def name(self):
        return self._name
