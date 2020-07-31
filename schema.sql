CREATE TABLE application (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE logged_entry (
    start DATETIME NOT NULL,
    end DATETIME NOT NULL,
    application_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    FOREIGN KEY(application_id) REFERENCES application(id)
);

