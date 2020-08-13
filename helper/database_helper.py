import sqlite3


def create_connection():
    conn = sqlite3.connect("test.db", detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn
