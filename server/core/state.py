from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from typing import Literal, assert_never

from core.days import study_day
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
from core.memory import Memory, review
from core.settings import Settings


@dataclass(frozen=True, slots=True)
class CardState:
    memory: Memory
    learned: date
    graduated: bool
    passed: bool
    lapses: int
    suspended: bool


@dataclass(frozen=True, slots=True)
class Mark:
    status: Literal["known", "ignored"]
    at: datetime


@dataclass(frozen=True, slots=True)
class State:
    introduced: Mapping[str, datetime]
    marks: Mapping[str, Mark]
    cards: Mapping[str, CardState]
    # Items whose first rung a lookup, miss or failed exercise made due on a study day.
    made_due: Mapping[str, date]


def items_of(card: str) -> tuple[str, ...]:
    subject = card.rsplit("/", 1)[0]
    return tuple(part.split("@")[0] for part in subject.split("+"))


def derive(events: Iterable[Event], settings: Settings) -> State:
    unique = {event.id: event for event in events}
    retracted: set[str] = set()
    for event in unique.values():
        match event.payload:
            case Retracted(event=target):
                retracted.add(target)
            case _:
                pass
    history = sorted(
        (e for e in unique.values() if e.id not in retracted), key=lambda e: (e.at, e.id)
    )

    introduced: dict[str, datetime] = {}
    marks: dict[str, Mark] = {}
    cards: dict[str, CardState] = {}
    made_due: dict[str, date] = {}

    for event in history:
        day = study_day(event.at, settings)
        match event.payload:
            case Introduced(item=item, reason=reason):
                introduced.setdefault(item, event.at)
                if reason == "reteach":
                    for card, state in cards.items():
                        if item in items_of(card):
                            cards[card] = replace(state, lapses=0, suspended=False)
                    made_due[item] = day
            case Reviewed(card=card, passed=passed, method=method) if method != "choice":
                cards[card] = _reviewed(cards.get(card), passed, event.at, settings)
                for item in items_of(card):
                    made_due.pop(item, None)
            case LookedUp(item=item) | Missed(item=item):
                made_due[item] = day + timedelta(days=1)
            case Exercised(passed=False, items=items):
                for item in items:
                    made_due[item] = day + timedelta(days=1)
            case Marked(item=item, status=status):
                if status == "unknown":
                    marks.pop(item, None)
                else:
                    marks[item] = Mark(status, event.at)
            case Reviewed() | Exercised() | Read() | Retracted():
                pass
            case _:
                assert_never(event.payload)

    return State(introduced, marks, cards, made_due)


def _reviewed(
    previous: CardState | None, passed: bool, at: datetime, settings: Settings
) -> CardState:
    day = study_day(at, settings)
    if previous is None:
        memory = review(None, passed, at, settings)
        return CardState(memory, day, graduated=False, passed=passed, lapses=0, suspended=False)

    overdue = study_day(previous.memory.due, settings) < day
    lapses = previous.lapses + (previous.graduated and not passed and not overdue)
    return CardState(
        memory=review(previous.memory, passed, at, settings),
        learned=previous.learned,
        graduated=previous.graduated or (passed and day > previous.learned),
        passed=passed,
        lapses=lapses,
        suspended=previous.suspended or lapses >= settings.lapses_before_suspension,
    )
