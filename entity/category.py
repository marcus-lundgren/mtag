import hashlib


class Category():
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
        #hash_as_int = int(hashlib.sha256(self._name.encode('utf-8')).hexdigest(), 16) % 101
        #color_from_hash = hash_as_int / 100
        #return color_from_hash, color_from_hash, color_from_hash
        hex_hash = hashlib.sha256(self._name.encode('utf-8')).hexdigest()
        return f"#{hex_hash[0:6]}"


