DROP TABLE IF EXISTS logged_entry;
DROP TABLE IF EXISTS application;
DROP TABLE IF EXISTS application_path;
DROP TABLE IF EXISTS tagged_entry;
DROP TABLE IF EXISTS category;

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

CREATE TABLE logged_entry (
    le_id INTEGER PRIMARY KEY AUTOINCREMENT,
    le_application_id INTEGER NOT NULL,
    le_title TEXT NOT NULL,
    le_start TIMESTAMP NOT NULL UNIQUE,
    le_last_update TIMESTAMP NOT NULL UNIQUE,
    FOREIGN KEY (le_application_id) REFERENCES application(a_id)
);

CREATE TABLE category (
    c_id INTEGER PRIMARY KEY AUTOINCREMENT,
    c_name TEXT NOT NULL UNIQUE
);

CREATE TABLE tagged_entry (
    te_id INTEGER PRIMARY KEY AUTOINCREMENT,
    te_category_id INTEGER NOT NULL,
    te_start TIMESTAMP NOT NULL UNIQUE,
    te_end TIMESTAMP NOT NULL UNIQUE,
    FOREIGN KEY (te_category_id) REFERENCES category(c_id)
);
