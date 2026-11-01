"""The user database: SQLite in WAL mode, migrated by numbered SQL files (011)."""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

MIGRATIONS = Path(__file__).parent / "migrations"
BUSY_TIMEOUT_MS = 5000


def open_database(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, autocommit=True, check_same_thread=False)
    db.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    db.execute("PRAGMA journal_mode = WAL")
    db.execute("PRAGMA foreign_keys = ON")
    _migrate(db)
    return db


@contextmanager
def transaction(db: sqlite3.Connection) -> Generator[sqlite3.Connection]:
    """All the writes inside take effect together or not at all."""
    db.execute("BEGIN IMMEDIATE")
    try:
        yield db
    except BaseException:
        db.execute("ROLLBACK")
        raise
    db.execute("COMMIT")


def _migrate(db: sqlite3.Connection) -> None:
    (version,) = db.execute("PRAGMA user_version").fetchone()
    for script in sorted(MIGRATIONS.glob("*.sql")):
        number = int(script.stem)
        if number > version:
            db.executescript(f"BEGIN; {script.read_text()} PRAGMA user_version = {number}; COMMIT;")
