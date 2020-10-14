import hashlib
from functools import lru_cache
from typing import Tuple


@lru_cache(maxsize=100)
def to_color_floats(text: str) -> Tuple:
    hex_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
    rs = hex_hash[0:2]
    gs = hex_hash[2:4]
    bs = hex_hash[4:6]
    return int(rs, 16) / 255, int(gs, 16) / 255, int(bs, 16) / 255
