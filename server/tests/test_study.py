from collections import Counter
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from api.library import GrammarView, PassageView, WordView
from api.study import CardStep, DoneStep, MeetingStep, PageStep, Step
from core.settings import Settings
from tests.server import NOW, OWNER, app_client, owner_database

LONGEST_SESSION = 100
STEP = TypeAdapter[CardStep | PageStep | MeetingStep | DoneStep](Step)


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    client = app_client(owner_database(tmp_path))
    client.post("/api/session", json=OWNER)
    return client


def answer(step: CardStep | PageStep | MeetingStep) -> dict[str, object]:
    """What a learner who knows everything does with a step."""
    match step:
        case CardStep(card=card, passage=passage):
            passage_id = None if passage is None else passage.id
            return {
                "kind": "reviewed",
                "card": card,
                "passed": True,
                "method": "self",
                "passage": passage_id,
            }
        case PageStep(item=item, reason=reason):
            return {"kind": "introduced", "item": item.id, "reason": reason}
        case MeetingStep(item=item, passage=passage):
            passage_id = None if passage is None else passage.id
            return {"kind": "introduced", "item": item.id, "reason": "new", "passage": passage_id}


def holds(passage: PassageView, item: str) -> bool:
    return any(item in span.items for span in passage.spans)


def test_a_first_session_meets_each_item_before_its_card_and_ends(client: TestClient) -> None:
    # Answers in the last few minutes, so each card's next learning step falls due after now.
    steps: list[CardStep | PageStep | MeetingStep] = []
    start = NOW - timedelta(minutes=5)
    for n in range(LONGEST_SESSION):
        step = STEP.validate_python(client.get("/api/study/next").json())
        if isinstance(step, DoneStep):
            break
        steps.append(step)
        event = {
            "id": f"e{n}",
            "at": (start + timedelta(seconds=n)).isoformat(),
            "payload": answer(step),
        }
        assert client.post("/api/events", json=[event]).json()["refused"] == []
    else:
        raise AssertionError(f"no end after {LONGEST_SESSION} steps")

    met: list[str] = []
    shown: Counter[str] = Counter()
    for step in steps:
        match step:
            case PageStep(item=item) | MeetingStep(item=item):
                met.append(item.id)
            case CardStep(card=card, item=item, passage=passage, spelling=spelling):
                assert item.id in met
                assert passage is None or holds(passage, item.id)
                if isinstance(item, WordView):
                    assert spelling in (*item.spellings, *item.readings)
                shown[card] += 1
    systems = [
        step
        for step in steps
        if isinstance(step.item, GrammarView) and step.item.grammar == "system"
    ]

    # The whole new budget, a system among it; each card once new and once, early, at its
    # next learning step.
    assert len(met) == len(set(met)) == Settings().new_budget
    assert systems
    assert set(shown.values()) == {2}


def test_settings_are_checked_and_take_effect_at_once(client: TestClient) -> None:
    assert client.get("/api/settings").json()["zone"] == "UTC"
    assert client.put("/api/settings", json={"zone": "Mars/Olympus"}).status_code == 422
    assert client.put("/api/settings", json={"new_budget": -1}).status_code == 422
    assert client.put("/api/settings", json={"colour": "red"}).status_code == 422
    assert STEP.validate_python(client.get("/api/study/next").json()).kind == "meeting"

    stored = client.put("/api/settings", json={"zone": "Europe/Istanbul", "new_budget": 0})
    assert stored.status_code == 200
    assert client.get("/api/settings").json()["zone"] == "Europe/Istanbul"
    assert STEP.validate_python(client.get("/api/study/next").json()).kind == "done"


def test_today_counts_what_is_left_and_what_is_done(client: TestClient) -> None:
    budget, passages = Settings().new_budget, Settings().reading_per_day
    fresh = client.get("/api/today").json()
    assert (fresh["reviews"], fresh["new"], fresh["reading"]) == (0, budget, passages)
    assert (fresh["reviewed"], fresh["met"]) == (0, 0)

    for n in range(2):
        step = STEP.validate_python(client.get("/api/study/next").json())
        assert not isinstance(step, DoneStep)
        when = (NOW - timedelta(minutes=5) + timedelta(seconds=n)).isoformat()
        client.post("/api/events", json=[{"id": f"e{n}", "at": when, "payload": answer(step)}])

    after = client.get("/api/today").json()
    assert (after["reviews"], after["new"], after["reviewed"], after["met"]) == (
        1,
        budget - 1,
        1,
        1,
    )
