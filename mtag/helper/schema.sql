-- DROP TABLE IF EXISTS logged_entry;
-- DROP TABLE IF EXISTS application_window;
-- DROP TABLE IF EXISTS application;
-- DROP TABLE IF EXISTS application_path;
-- DROP TABLE IF EXISTS tagged_entry;
-- DROP TABLE IF EXISTS category;
-- DROP TABLE IF EXISTS activity_entry;

CREATE TABLE application_path (
    ap_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ap_path TEXT NOT NULL UNIQUE
);

CREATE TABLE application (
    a_id INTEGER PRIMARY KEY AUTOINCREMENT,
    a_name TEXT NOT NULL,
    a_path_id INTEGER NOT NULL,
    FOREIGN KEY (a_path_id) REFERENCES application_path(ap_id),
    UNIQUE (a_name, a_path_id)
);

CREATE TABLE application_window (
    aw_id INTEGER PRIMARY KEY AUTOINCREMENT,
    aw_title TEXT NOT NULL,
    aw_application_id INTEGER NOT NULL,
    FOREIGN KEY (aw_application_id) REFERENCES application(a_id),
    UNIQUE (aw_application_id, aw_title)
);

CREATE TABLE logged_entry (
    le_id INTEGER PRIMARY KEY AUTOINCREMENT,
    le_application_window_id INTEGER NOT NULL,
    le_start INTEGER NOT NULL UNIQUE,
    le_last_update INTEGER NOT NULL UNIQUE,
    FOREIGN KEY (le_application_window_id) REFERENCES application_window(aw_id)
);

CREATE TABLE category (
    c_id INTEGER PRIMARY KEY AUTOINCREMENT,
    c_name TEXT NOT NULL UNIQUE
);

CREATE TABLE tagged_entry (
    te_id INTEGER PRIMARY KEY AUTOINCREMENT,
    te_category_id INTEGER NOT NULL,
    te_start INTEGER NOT NULL UNIQUE,
    te_end INTEGER NOT NULL UNIQUE,
    FOREIGN KEY (te_category_id) REFERENCES category(c_id)
);

CREATE TABLE activity_entry (
    ae_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ae_start INTEGER NOT NULL UNIQUE,
    ae_last_update INTEGER NOT NULL UNIQUE,
    ae_active INTEGER NOT NULL
);
