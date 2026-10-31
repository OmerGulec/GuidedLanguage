import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from typing import Literal, assert_never

from core.cards import FIRST_RUNGS, Card
from core.days import study_day
from core.events import (
    Event,
    Exercised,
    Introduced,
    LookedUp,
    Marked,
    Missed,
    Modality,
    Read,
    Retracted,
    Reviewed,
)
from core.memory import Memory, review
from core.settings import Settings

# Midway on the scheduler's 1 to 10 difficulty scale, for memories that never had a review.
STARTING_DIFFICULTY = 5.0


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
    read: Mapping[Modality, frozenset[str]]


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
    read: dict[Modality, set[str]] = {"reading": set(), "listening": set()}

    for event in history:
        day = study_day(event.at, settings)
        match event.payload:
            case Introduced(item=item, reason=reason):
                introduced.setdefault(item, event.at)
                if reason == "reteach":
                    for card, state in cards.items():
                        if item in Card.parse(card).items:
                            cards[card] = replace(state, lapses=0, suspended=False)
                    made_due[item] = day
            case Reviewed(card=card, passed=passed, method=method) if method != "choice":
                previous = cards.get(card) or _marked_start(card, marks, settings)
                cards[card] = _reviewed(previous, passed, event.at, settings)
                for item in Card.parse(card).items:
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
            case Read(passage=passage, modality=modality):
                read[modality].add(passage)
            case Reviewed() | Exercised() | Retracted():
                pass
            case _:
                assert_never(event.payload)

    passages_read: dict[Modality, frozenset[str]] = {m: frozenset(p) for m, p in read.items()}
    return State(introduced, marks, cards, made_due, passages_read)


def starting(item: str, mark: Mark, settings: Settings) -> CardState:
    """The memory of a first rung whose item was marked known: as if learned long ago."""
    digest = hashlib.sha256(item.encode()).digest()
    spread = int.from_bytes(digest[:4]) / 2**32 * settings.marked_spread_days
    stability = settings.marked_stability_days + spread
    memory = Memory(
        stability=stability,
        difficulty=STARTING_DIFFICULTY,
        phase="review",
        step=None,
        due=mark.at + timedelta(days=stability),
        last_review=mark.at,
    )
    learned = study_day(mark.at, settings)
    return CardState(memory, learned, graduated=True, passed=True, lapses=0, suspended=False)


def _marked_start(card: str, marks: Mapping[str, Mark], settings: Settings) -> CardState | None:
    parsed = Card.parse(card)
    if parsed.rung not in FIRST_RUNGS:
        return None
    for item in parsed.items:
        mark = marks.get(item)
        if mark is not None and mark.status == "known":
            return starting(item, mark, settings)
    return None


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
