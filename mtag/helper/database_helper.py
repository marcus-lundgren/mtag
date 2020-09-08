import sqlite3
import os


def create_connection():
    home_path = os.environ["HOME"]
    conn = sqlite3.connect(f"{home_path}/.config/mtag.db", detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn
