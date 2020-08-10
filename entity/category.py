from helper import color_helper


class Category:
    def __init__(self, name: str, db_id: int = None):
        self._db_id = db_id
        self._name = name

    @property
    def db_id(self):
        return self._db_id

    @property
    def name(self):
        return self._name

    @property
    def color_rgb(self):
        return color_helper.to_color(self._name)
