"""Each account's learning history (013)."""

import json
import sqlite3
from collections.abc import Iterable
from dataclasses import asdict
from datetime import datetime

from pydantic import TypeAdapter

from core.events import (
    Event,
    Exercised,
    Introduced,
    LookedUp,
    Marked,
    Missed,
    Payload,
    Read,
    Retracted,
    Reviewed,
)
from store.database import transaction

# The shape events are written in; older shapes are upgraded when read, once there are any.
VERSION = 1
_KINDS: tuple[type[Payload], ...] = (
    Introduced,
    Reviewed,
    LookedUp,
    Read,
    Exercised,
    Missed,
    Marked,
    Retracted,
)
_ADAPTERS = {kind.__name__: TypeAdapter[Payload](kind) for kind in _KINDS}


def append(db: sqlite3.Connection, account: int, events: Iterable[Event], arrived: datetime) -> int:
    """Add events, ignoring any whose id the account already has; returns how many were new."""
    rows = [
        (
            account,
            e.id,
            e.at.isoformat(),
            arrived.isoformat(),
            e.origin,
            VERSION,
            type(e.payload).__name__,
            json.dumps(asdict(e.payload), ensure_ascii=False),
        )
        for e in events
    ]
    with transaction(db):
        before = db.total_changes
        db.executemany(
            "INSERT OR IGNORE INTO events"
            " (account, id, at, arrived, origin, version, kind, payload)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        return db.total_changes - before


def history(db: sqlite3.Connection, account: int, after: int = 0) -> list[tuple[int, Event]]:
    """The account's events after a sequence number, each with its own, in arrival order."""
    rows = db.execute(
        "SELECT sequence, id, at, origin, kind, payload FROM events"
        " WHERE account = ? AND sequence > ? ORDER BY sequence",
        (account, after),
    )
    return [
        (sequence, Event(id, datetime.fromisoformat(at), origin, _ADAPTERS[kind].validate_json(p)))
        for sequence, id, at, origin, kind, p in rows
    ]
