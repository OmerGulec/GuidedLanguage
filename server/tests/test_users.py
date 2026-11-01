import sqlite3
from datetime import timedelta
from pathlib import Path

import pytest

from core.events import (
    Event,
    Exercised,
    Introduced,
    LookedUp,
    Marked,
    Missed,
    Read,
    Retracted,
    Reviewed,
)
from store.accounts import SESSION_LENGTH, account_of, create_account, sign_in, sign_out
from store.database import open_database
from store.events import append, history
from tests.history import at


@pytest.fixture
def db(tmp_path: Path) -> sqlite3.Connection:
    return open_database(tmp_path / "users.sqlite")


def test_only_the_right_password_opens_a_session_and_it_lasts_until_it_expires(
    db: sqlite3.Connection,
) -> None:
    now = at(1, 9)
    owner = create_account(db, "Owner@Example.com ", "kana and kanji", now)
    assert create_account(db, "owner@example.com", "other", now) is None

    assert sign_in(db, "owner@example.com", "wrong", now) is None
    assert sign_in(db, "nobody@example.com", "kana and kanji", now) is None
    token = sign_in(db, "owner@example.com", "kana and kanji", now)
    assert token is not None
    assert account_of(db, token, now) == owner
    assert account_of(db, token, now + SESSION_LENGTH) is None
    assert account_of(db, "not a token", now) is None

    sign_out(db, token)
    assert account_of(db, token, now) is None


def test_a_copy_of_the_database_holds_no_password_or_session_token(
    db: sqlite3.Connection,
) -> None:
    create_account(db, "owner@example.com", "kana and kanji", at(1, 9))
    token = sign_in(db, "owner@example.com", "kana and kanji", at(1, 9))
    assert token is not None

    dump = "\n".join(db.iterdump())
    assert "kana and kanji" not in dump
    assert token not in dump


def test_every_kind_of_event_comes_back_as_it_went_in_once_per_id(db: sqlite3.Connection) -> None:
    owner = create_account(db, "owner@example.com", "pw", at(1, 9))
    other = create_account(db, "other@example.com", "pw", at(1, 9))
    assert owner is not None and other is not None
    payloads = [
        Introduced("w:1", "new", passage="p1"),
        Reviewed(
            "w:1@分かる/recognize", passed=False, method="typed", answer="わかる", passage="p2"
        ),
        LookedUp("w:1", "p3", surface="分かった", context="よく分かった。"),
        Read("p3", "reading"),
        Exercised("p3", "dictation", passed=True, items=("w:1", "w:2")),
        Missed("w:2", "p3", surface="猫", context="猫がいる。"),
        Marked("wa.topic", "known", "hand"),
        Retracted("e2"),
    ]
    events = [
        Event(f"e{n}", at(1, 9) + timedelta(seconds=n), "ours", p) for n, p in enumerate(payloads)
    ]

    assert append(db, owner, events, at(1, 10)) == len(events)
    assert append(db, owner, events[:3], at(1, 11)) == 0
    assert append(db, other, events[:1], at(1, 11)) == 1

    stored = history(db, owner)
    assert [event for _, event in stored] == events
    assert [event for _, event in history(db, owner, after=stored[-2][0])] == events[-1:]
