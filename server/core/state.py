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
# Marks nobody has checked: their first review comes sooner (014).
DOUBTFUL = frozenset({"hand", "course"})


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
    reason: Literal["hand", "placement", "course", "import"]


@dataclass(frozen=True, slots=True)
class State:
    introduced: Mapping[str, datetime]
    marks: Mapping[str, Mark]
    cards: Mapping[str, CardState]
    # Items whose first rung a lookup, miss or failed exercise made due on a study day.
    made_due: Mapping[str, date]
    read: Mapping[Modality, frozenset[str]]
    # Items whose mark a failed first review withdrew, by study day (014).
    withdrawn: Mapping[str, date]


EMPTY = State({}, {}, {}, {}, {"reading": frozenset(), "listening": frozenset()}, {})


def derive(events: Iterable[Event], settings: Settings) -> State:
    unique = {event.id: event for event in events}
    retracted: set[str] = set()
    for event in unique.values():
        match event.payload:
            case Retracted(event=target):
                retracted.add(target)
            case _:
                pass
    return advance(EMPTY, (e for e in unique.values() if e.id not in retracted), settings)


def advance(state: State, events: Iterable[Event], settings: Settings) -> State:
    """Continue a state with events that all come after its history; derive handles the rest."""
    introduced = dict(state.introduced)
    marks = dict(state.marks)
    cards = dict(state.cards)
    made_due = dict(state.made_due)
    read: dict[Modality, set[str]] = {m: set(p) for m, p in state.read.items()}
    withdrawn = dict(state.withdrawn)

    for event in sorted(events, key=lambda e: (e.at, e.id)):
        day = study_day(event.at, settings)
        match event.payload:
            case Introduced(item=item, reason=reason):
                introduced.setdefault(item, event.at)
                if reason == "reteach":
                    for card, held in cards.items():
                        if item in Card.parse(card).items:
                            cards[card] = replace(held, lapses=0, suspended=False)
                    made_due[item] = day
            case Reviewed(card=card, passed=passed, method=method) if method != "choice":
                marked = None if card in cards else _marked_item(card, marks)
                if marked is not None and not passed:
                    # A failed first review refutes the mark: memory restarts from real reviews
                    # and the item is re-taught, as a suspended one is (014).
                    del marks[marked]
                    withdrawn[marked] = day
                    fresh = _reviewed(None, passed, event.at, settings)
                    cards[card] = replace(fresh, suspended=True)
                else:
                    start = None if marked is None else starting(marked, marks[marked], settings)
                    cards[card] = _reviewed(cards.get(card) or start, passed, event.at, settings)
                for item in Card.parse(card).items:
                    made_due.pop(item, None)
            case LookedUp(item=item) | Missed(item=item):
                made_due[item] = day + timedelta(days=1)
            case Exercised(passed=False, items=items):
                for item in items:
                    made_due[item] = day + timedelta(days=1)
            case Marked(item=item, status=status, reason=reason):
                if status == "unknown":
                    marks.pop(item, None)
                else:
                    marks[item] = Mark(status, event.at, reason)
            case Read(passage=passage, modality=modality):
                read[modality].add(passage)
            case Reviewed() | Exercised() | Retracted():
                pass
            case _:
                assert_never(event.payload)

    passages_read: dict[Modality, frozenset[str]] = {m: frozenset(p) for m, p in read.items()}
    return State(introduced, marks, cards, made_due, passages_read, withdrawn)


def starting(item: str, mark: Mark, settings: Settings) -> CardState:
    """The memory of a first rung whose item was marked known: as if learned long ago. A mark
    nobody has checked keeps that memory but comes up for review within a few weeks (014)."""
    digest = hashlib.sha256(item.encode()).digest()
    place = int.from_bytes(digest[:4]) / 2**32
    stability = settings.marked_stability_days + place * settings.marked_spread_days
    wait = place * settings.doubtful_review_days if mark.reason in DOUBTFUL else stability
    memory = Memory(
        stability=stability,
        difficulty=STARTING_DIFFICULTY,
        phase="review",
        step=None,
        due=mark.at + timedelta(days=wait),
        last_review=mark.at,
    )
    learned = study_day(mark.at, settings)
    return CardState(memory, learned, graduated=True, passed=True, lapses=0, suspended=False)


def _marked_item(card: str, marks: Mapping[str, Mark]) -> str | None:
    """The item whose mark known gives this first rung its starting memory."""
    parsed = Card.parse(card)
    if parsed.rung not in FIRST_RUNGS:
        return None
    for item in parsed.items:
        mark = marks.get(item)
        if mark is not None and mark.status == "known":
            return item
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
