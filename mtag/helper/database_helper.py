import sqlite3
import os


def create_connection():
    home_path = os.environ["HOME"]
    config_path = f"{home_path}/.config/mtag/"
    if not os.path.exists(config_path):
        os.mkdir(config_path)

    database_file_path = os.path.join(config_path, "mtag.db")
    schema_script_needed = not os.path.exists(database_file_path)

    conn = sqlite3.connect(database_file_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row

    if schema_script_needed:
        schema_file_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        schema_file = open(file=schema_file_path, mode="rt")
        schema_script = schema_file.read()
        schema_file.close()

        conn.executescript(schema_script)

    return conn
