import hashlib
from functools import lru_cache
from typing import Tuple


def activity_to_color_floats(active: bool) -> Tuple[float, float, float]:
    return (0.14, 0.78, 0.14) if active else (0.5, 0.5, 0.5)


def activity_to_text_color_floats(active: bool) -> Tuple[float, float, float]:
    return (0.12, 0.93, 0.12) if active else (0.75, 0.75, 0.75)


@lru_cache(maxsize=100)
def to_color_floats(text: str) -> Tuple[float, float, float]:
    hex_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
    rs = hex_hash[0:2]
    gs = hex_hash[2:4]
    bs = hex_hash[4:6]
    return int(rs, 16) / 255, int(gs, 16) / 255, int(bs, 16) / 255
