from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import pytest

from api.app import create_app
from core import events as core
from store.accounts import create_account
from store.database import open_database
from store.events import history
from tests.history import at

NOW = at(1, 9)
OWNER = {"email": "owner@example.com", "password": "kana and kanji"}

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def users(tmp_path: Path) -> Path:
    path = tmp_path / "users.sqlite"
    create_account(open_database(path), OWNER["email"], OWNER["password"], NOW)
    return path


@pytest.fixture
async def client(users: Path) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=create_app(users, clock=lambda: NOW))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def post(client: httpx.AsyncClient, path: str, body: object) -> httpx.Response:
    return await client.post(path, json=body)


def event(id: str, when: datetime, **payload: object) -> dict[str, object]:
    return {"id": id, "at": when.isoformat(), "payload": payload}


async def test_events_need_a_session_and_signing_out_ends_it(client: httpx.AsyncClient) -> None:
    batch = [event("e1", NOW, kind="read", passage="p1", modality="reading")]
    assert (await post(client, "/api/events", batch)).status_code == 401

    wrong = await post(client, "/api/session", OWNER | {"password": "no"})
    assert wrong.status_code == 401
    assert (await post(client, "/api/session", OWNER)).status_code == 204
    assert (await post(client, "/api/events", batch)).status_code == 200

    token = client.cookies["session"]
    await client.delete("/api/session")
    assert (await post(client, "/api/events", batch)).status_code == 401
    client.cookies.set("session", token)
    assert (await post(client, "/api/events", batch)).status_code == 401


async def test_events_are_kept_once_with_their_own_instant_unless_it_is_ahead(
    client: httpx.AsyncClient, users: Path
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
    await post(client, "/api/session", OWNER)

    assert (await post(client, "/api/events", batch)).json() == {"added": 7, "refused": ["e8"]}
    assert (await post(client, "/api/events", batch[:3])).json() == {"added": 0, "refused": []}

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


async def test_a_malformed_batch_is_refused_whole(client: httpx.AsyncClient) -> None:
    unknown_kind = [event("e1", NOW, kind="imported", item="w:1")]
    no_zone = [event("e1", NOW, kind="read", passage="p1", modality="reading")]
    no_zone[0]["at"] = "2026-11-01T09:00:00"
    await post(client, "/api/session", OWNER)

    assert (await post(client, "/api/events", unknown_kind)).status_code == 422
    assert (await post(client, "/api/events", no_zone)).status_code == 422
