-- Users table. The database itself enforces some rules as a second line of defense:
--   * usernames are unique, case-insensitively ("Alice" and "alice" are the same user)
--   * role can only ever be 'User' or 'Admin', and defaults to the least-privileged 'User'
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'User' CHECK (role IN ('User', 'Admin')),
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    last_login_at TEXT
);
