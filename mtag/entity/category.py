from typing import Optional


class Category:
    def __init__(self, name: str, url: Optional[str] = None, db_id: Optional[int] = None, parent_id: Optional[int] = None):
        self.db_id = db_id
        self.name = name
        self.url = url
        self.parent_id = parent_id
