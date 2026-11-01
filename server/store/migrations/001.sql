CREATE TABLE accounts (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    created TEXT NOT NULL
);

-- A session is found by the hash of its cookie, so a copy of the database opens no sessions.
CREATE TABLE sessions (
    token TEXT PRIMARY KEY,
    account INTEGER NOT NULL REFERENCES accounts ON DELETE CASCADE,
    expires TEXT NOT NULL
);

CREATE TABLE settings (
    account INTEGER PRIMARY KEY REFERENCES accounts ON DELETE CASCADE,
    value TEXT NOT NULL
);

-- Learning history (013). The client makes the id and the instant; the sequence number is
-- only a sync cursor, and arrival is kept so a client with a wrong clock can be found.
CREATE TABLE events (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    account INTEGER NOT NULL REFERENCES accounts ON DELETE CASCADE,
    id TEXT NOT NULL,
    at TEXT NOT NULL,
    arrived TEXT NOT NULL,
    origin TEXT NOT NULL,
    version INTEGER NOT NULL,
    kind TEXT NOT NULL,
    payload TEXT NOT NULL,
    UNIQUE (account, id)
);
