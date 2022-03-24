import sqlite3
import os
import logging
from mtag.helper import filesystem_helper


def create_connection() -> sqlite3.Connection:
    userdata_path = filesystem_helper.get_userdata_path()
    database_file_path = os.path.join(userdata_path, "mtag.db")
    schema_script_needed = not os.path.exists(database_file_path)

    conn = sqlite3.connect(database_file_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")

    if schema_script_needed:
        logging.info("No database found. Creating it.")
        schema_file_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        schema_file = open(file=schema_file_path, mode="rt")
        schema_script = schema_file.read()
        schema_file.close()

        conn.executescript(schema_script)

    _update_if_needed(conn=conn)

    return conn


def _update_if_needed(conn: sqlite3.Connection):
    cursor = conn.execute("SELECT COUNT(*) as version_exist FROM sqlite_master WHERE type='table' AND name='version'")
    version_table_exists = cursor.fetchone()["version_exist"] == 1
    if not version_table_exists:
        logging.info("Updating database to version 1")
        cursor.execute("ALTER TABLE category ADD COLUMN c_url TEXT NOT NULL DEFAULT ''")
        cursor.execute("CREATE TABLE version(v_version INTEGER PRIMARY KEY NOT NULL)")
        cursor.execute("INSERT INTO version VALUES (1)")
        conn.commit()
        logging.info("Database updated to version 1")

    cursor = conn.execute("SELECT MAX(v_version) AS current_version FROM version")
    database_version = cursor.fetchone()["current_version"]
    cursor.close()

    if database_version < 2:
        logging.info("Updating database to version 2")

        old_isolation_level = conn.isolation_level
        conn.isolation_level = "EXCLUSIVE"
        cursor = conn.cursor()

        # https://www.sqlite.org/lang_altertable.html
        #  1. If foreign key constraints are enabled,
        #     disable them using PRAGMA foreign_keys=OFF.
        cursor.execute("PRAGMA foreign_keys=OFF")

        # 2. Start a transaction
        cursor.execute("BEGIN")

        # 3.  Remember the format of all indexes, triggers, and views
        #     associated with table X. This information will be needed in
        #     step 8 below. One way to do this is to run a query like the
        #     following: SELECT type, sql FROM sqlite_schema WHERE tbl_name='X'.

        # N/A

        # 4. Use CREATE TABLE to construct a new table "new_X" that is in
        #    the desired revised format of table X. Make sure that the name
        #    "new_X" does not collide with any existing table name, of course.
        cursor.execute("""
CREATE TABLE new_category (
    c_id INTEGER PRIMARY KEY AUTOINCREMENT,
    c_name TEXT NOT NULL,
    c_url TEXT NOT NULL DEFAULT '',
    c_parent_id INTEGER DEFAULT NULL,
    FOREIGN KEY (c_parent_id) REFERENCES new_category(c_id),
    UNIQUE (c_name, c_parent_id)
)""")

        # 5. Transfer content from X into new_X using a statement like: INSERT INTO new_X SELECT ... FROM X.
        cursor.execute("""
INSERT INTO new_category(c_id, c_name, c_url)
 SELECT category.c_id, category.c_name, category.c_url FROM category""")

        # 6. Drop the old table
        cursor.execute("DROP TABLE category")

        # 7. Change the name of new_X to X using: ALTER TABLE new_X RENAME TO X.
        cursor.execute("ALTER TABLE new_category RENAME TO category")

        # 8. Use CREATE INDEX, CREATE TRIGGER, and CREATE VIEW to reconstruct indexes,
        #    triggers, and views associated with table X. Perhaps use the old format
        #    of the triggers, indexes, and views saved from step 3 above as a guide,
        #    making changes as appropriate for the alteration.

        # N/A

        # 9. If any views refer to table X in a way that is affected by the schema change,
        #    then drop those views using DROP VIEW and recreate them with whatever changes
        #    are necessary to accommodate the schema change using CREATE VIEW.

        # N/A

        # 10. If foreign key constraints were originally enabled then run
        #     PRAGMA foreign_key_check to verify that the schema change did not break
        #     any foreign key constraints.
        cursor.execute("PRAGMA foreign_key_check")

        # 11. Commit the transaction started in step 2.
        cursor.execute("COMMIT")

        # 12. If foreign keys constraints were originally enabled, reenable them now.
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("INSERT INTO version VALUES (2)")
        conn.commit()
        conn.isolation_level = old_isolation_level
        logging.info("Database updated to version 2")

