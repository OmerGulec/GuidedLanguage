"""Each account's settings: one plain row, not events (013)."""

import sqlite3


def read_settings(db: sqlite3.Connection, account: int) -> str | None:
    row = db.execute("SELECT value FROM settings WHERE account = ?", (account,)).fetchone()
    return None if row is None else row[0]


def write_settings(db: sqlite3.Connection, account: int, value: str) -> None:
    db.execute(
        "INSERT INTO settings VALUES (?, ?)"
        " ON CONFLICT (account) DO UPDATE SET value = excluded.value",
        (account, value),
    )
