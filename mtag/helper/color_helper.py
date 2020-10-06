import hashlib
from functools import lru_cache


@lru_cache(maxsize=100)
def to_color(text: str) -> str:
    hex_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
    color_string = f"#{hex_hash[0:6]}"
    return color_string
