import sqlite3
import os
from mtag.helper import filesystem_helper


def create_connection() -> sqlite3.Connection:
    userdata_path = filesystem_helper.get_userdata_path()
    database_file_path = os.path.join(userdata_path, "mtag.db")
    schema_script_needed = not os.path.exists(database_file_path)

    conn = sqlite3.connect(database_file_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row

    if schema_script_needed:
        print("No database found. Creating it.")
        schema_file_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        schema_file = open(file=schema_file_path, mode="rt")
        schema_script = schema_file.read()
        schema_file.close()

        conn.executescript(schema_script)

    _update_if_needed(conn=conn)

    return conn


def _update_if_needed(conn=sqlite3.Connection):
    cursor = conn.execute("SELECT COUNT(*) as version_exist FROM sqlite_master WHERE type='table' AND name='version'")
    version_table_exists = cursor.fetchone()["version_exist"] == 1
    if not version_table_exists:
        print("Updating database to version 1")
        cursor.execute("ALTER TABLE category ADD COLUMN c_url TEXT NOT NULL DEFAULT ''")
        cursor.execute("CREATE TABLE version(v_version INTEGER PRIMARY KEY NOT NULL)")
        cursor.execute("INSERT INTO version VALUES (1)")
        conn.commit()
