import hashlib


def to_color(text: str) -> str:
    hex_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
    return f"#{hex_hash[0:6]}"
