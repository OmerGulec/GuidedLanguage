import sqlite3
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from api.learners import Learners
from core.events import Event, Introduced, Payload, Retracted, Reviewed
from core.state import derive
from store.accounts import create_account
from store.database import open_database
from store.events import append, history
from tests.history import TOKYO, at

CARD = "w:1@分かる/recognize"


@pytest.fixture
def db(tmp_path: Path) -> sqlite3.Connection:
    return open_database(tmp_path / "users.sqlite")


def test_the_kept_state_always_equals_deriving_the_whole_history(db: sqlite3.Connection) -> None:
    owner = create_account(db, "owner@example.com", "pw", at(1, 9))
    assert owner is not None
    learners = Learners(db)
    count = 0

    def add(day: int, payload: Payload) -> None:
        nonlocal count
        count += 1
        when = at(day, 9) + timedelta(minutes=count)
        append(db, owner, [Event(f"e{count}", when, "ours", payload)], at(9, 9))
        everything = [event for _, event in history(db, owner)]
        assert learners.state(owner, TOKYO) == derive(everything, TOKYO)

    add(1, Introduced("w:1", "new"))
    add(1, Reviewed(CARD, passed=True, method="self"))
    add(3, Reviewed(CARD, passed=True, method="self"))
    add(2, Reviewed(CARD, passed=False, method="self"))
    add(4, Reviewed(CARD, passed=True, method="self"))
    add(4, Retracted("e5"))
    add(5, Reviewed(CARD, passed=True, method="self"))

    later_day = replace(TOKYO, day_start_hour=TOKYO.day_start_hour + 6)
    everything = [event for _, event in history(db, owner)]
    assert learners.state(owner, later_day) == derive(everything, later_day)
    assert learners.state(owner, later_day) != derive(everything, TOKYO)
