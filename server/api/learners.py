"""Each learner's state, kept in memory so a request does not replay their whole history."""

import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime

from core.events import Event, Retracted
from core.settings import Settings
from core.state import State, advance, derive
from store.events import history


@dataclass(frozen=True, slots=True)
class _Held:
    state: State
    # The last event applied, in arrival order and in replay order; None before any.
    sequence: int
    latest: tuple[datetime, str] | None


class Learners:
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db
        self._held: dict[int, _Held] = {}
        self._lock = threading.Lock()

    def state(self, account: int, settings: Settings) -> State:
        """Advanced with new events only when they all come after what it holds and retract
        nothing; an undo, an import of older history or a late event re-derives (013)."""
        with self._lock:
            held = self._held.get(account)
            after = 0 if held is None else held.sequence
            new = history(self._db, account, after)
            if held is not None and not new:
                return held.state

            events = [event for _, event in new]
            if held is not None and _extends(held, events):
                state = advance(held.state, events, settings)
                latest = max(_order(e) for e in events)
            else:
                everything = [event for _, event in history(self._db, account)]
                state = derive(everything, settings)
                latest = max((_order(e) for e in everything), default=None)
            sequence = new[-1][0] if new else after
            self._held[account] = _Held(state, sequence, latest)
            return state

    def forget(self, account: int) -> None:
        """For when what derivation depends on changes, such as the learner's settings."""
        with self._lock:
            self._held.pop(account, None)


def _extends(held: _Held, events: list[Event]) -> bool:
    return all(
        (held.latest is None or _order(e) > held.latest) and not isinstance(e.payload, Retracted)
        for e in events
    )


def _order(event: Event) -> tuple[datetime, str]:
    return event.at, event.id
