from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from core import events as core
from store.accounts import create_account
from store.database import open_database
from store.events import history
from tests.history import at

NOW = at(1, 9)
OWNER = {"email": "owner@example.com", "password": "kana and kanji"}


@pytest.fixture
def users(tmp_path: Path) -> Path:
    path = tmp_path / "users.sqlite"
    create_account(open_database(path), OWNER["email"], OWNER["password"], NOW)
    return path


@pytest.fixture
def client(users: Path) -> TestClient:
    return TestClient(create_app(users, clock=lambda: NOW))


def event(id: str, when: datetime, **payload: object) -> dict[str, object]:
    return {"id": id, "at": when.isoformat(), "payload": payload}


def test_events_need_a_session_and_signing_out_ends_it(client: TestClient) -> None:
    batch = [event("e1", NOW, kind="read", passage="p1", modality="reading")]
    assert client.post("/api/events", json=batch).status_code == 401

    assert client.post("/api/session", json=OWNER | {"password": "no"}).status_code == 401
    assert client.post("/api/session", json=OWNER).status_code == 204
    assert client.post("/api/events", json=batch).status_code == 200

    token = client.cookies["session"]
    client.delete("/api/session")
    assert client.post("/api/events", json=batch).status_code == 401
    client.cookies.set("session", token)
    assert client.post("/api/events", json=batch).status_code == 401


def test_events_are_kept_once_with_their_own_instant_unless_it_is_ahead(
    client: TestClient, users: Path
) -> None:
    card = "w:1@分かる/recognize"
    earlier = NOW - timedelta(minutes=2)
    batch = [
        event("e1", earlier, kind="introduced", item="w:1", reason="new"),
        event("e2", NOW, kind="reviewed", card=card, passed=True, method="self", passage="p1"),
        event("e3", NOW, kind="looked-up", item="w:2", passage="p1", surface="猫", context="猫だ"),
        event("e4", NOW, kind="missed", item="w:2", passage="p1", surface="猫", context="猫だ"),
        event("e5", NOW, kind="marked", item="wa.topic", status="known"),
        event("e6", NOW, kind="read", passage="p1", modality="reading"),
        event("e7", NOW, kind="retracted", event="e5"),
        event("e8", NOW + timedelta(minutes=5), kind="read", passage="p2", modality="reading"),
    ]
    client.post("/api/session", json=OWNER)

    assert client.post("/api/events", json=batch).json() == {"added": 7, "refused": ["e8"]}
    assert client.post("/api/events", json=batch[:3]).json() == {"added": 0, "refused": []}

    owner = 1
    stored = [e for _, e in history(open_database(users), owner)]
    assert [(e.id, e.at, e.origin) for e in stored[:2]] == [
        ("e1", earlier, "ours"),
        ("e2", NOW, "ours"),
    ]
    assert [e.payload for e in stored] == [
        core.Introduced("w:1", "new"),
        core.Reviewed(card, passed=True, method="self", passage="p1"),
        core.LookedUp("w:2", "p1", "猫", "猫だ"),
        core.Missed("w:2", "p1", "猫", "猫だ"),
        core.Marked("wa.topic", "known", "hand"),
        core.Read("p1", "reading"),
        core.Retracted("e5"),
    ]


def test_a_malformed_batch_is_refused_whole(client: TestClient) -> None:
    unknown_kind = [event("e1", NOW, kind="imported", item="w:1")]
    no_zone = [event("e1", NOW, kind="read", passage="p1", modality="reading")]
    no_zone[0]["at"] = "2026-11-01T09:00:00"
    client.post("/api/session", json=OWNER)

    assert client.post("/api/events", json=unknown_kind).status_code == 422
    assert client.post("/api/events", json=no_zone).status_code == 422
