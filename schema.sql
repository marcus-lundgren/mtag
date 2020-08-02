CREATE TABLE application_path (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL
);

CREATE TABLE application (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    path_id INTEGER NOT NULL,
    FOREIGN KEY (path_id) REFERENCES application_path(id)
);

CREATE TABLE logged_entry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    start DATETIME NOT NULL,
    end DATETIME NOT NULL,
    FOREIGN KEY (application_id) REFERENCES application(id)
);
