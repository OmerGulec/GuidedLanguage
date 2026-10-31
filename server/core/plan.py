from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import numpy as np
from numpy.typing import NDArray

from core.candidates import Ranking, candidates
from core.cards import FIRST_RUNGS, RUNGS, Card, Goal
from core.days import next_boundary, study_day
from core.events import Modality
from core.pack import Pack
from core.settings import Settings
from core.state import State

LISTENING_GOALS: frozenset[Goal] = frozenset({"listener", "complete"})


@dataclass(frozen=True, slots=True)
class Situation:
    sound: bool = True
    keyboard: bool = True


@dataclass(frozen=True, slots=True)
class Plan:
    reviews: tuple[str, ...]
    reteach: tuple[str, ...]
    new: tuple[str, ...]
    passages: Mapping[Modality, tuple[str, ...]]


def plan(
    state: State,
    unknowns: Mapping[Modality, NDArray[np.float64]],
    pack: Pack,
    ranking: Ranking,
    goal: Goal,
    situation: Situation,
    settings: Settings,
    now: datetime,
) -> Plan:
    suspended = (Card.parse(card).items for card, held in state.cards.items() if held.suspended)
    reteach = sorted({item for items in suspended for item in items})

    today = study_day(now, settings)
    started_today = sum(held.learned == today for held in state.cards.values())
    budget = max(0, settings.new_budget - started_today - len(reteach))
    new = [card for card in candidates(state, ranking, goal) if _possible(card, situation)]

    modalities: list[Modality] = ["reading"]
    if goal in LISTENING_GOALS and situation.sound:
        modalities.append("listening")

    return Plan(
        reviews=_reviews(state, ranking, situation, settings, now),
        reteach=tuple(reteach),
        new=tuple(new[:budget]),
        passages={m: _passages(unknowns[m], pack, state.read[m], settings) for m in modalities},
    )


def _possible(card: str, situation: Situation) -> bool:
    rung = RUNGS[Card.parse(card).rung]
    return (situation.sound or not rung.needs_sound) and (
        situation.keyboard or not rung.needs_keyboard
    )


def _reviews(
    state: State, ranking: Ranking, situation: Situation, settings: Settings, now: datetime
) -> tuple[str, ...]:
    today = study_day(now, settings)
    end_of_day = next_boundary(now, settings)
    spacing = timedelta(days=settings.spacing_days)

    latest: dict[str, tuple[datetime, str]] = {}
    for card_id, held in state.cards.items():
        for item in Card.parse(card_id).items:
            if item not in latest or held.memory.last_review > latest[item][0]:
                latest[item] = (held.memory.last_review, card_id)

    def spaced(item: str, card_id: str) -> bool:
        reviewed_at, reviewed_card = latest[item]
        return reviewed_card == card_id or study_day(reviewed_at, settings) + spacing <= today

    # The cap limits reviews of learned cards. Same-day learning steps are never capped, or
    # reaching the cap would leave just-learned words half taught.
    reviewed_today = sum(
        study_day(held.memory.last_review, settings) == today and held.learned < today
        for held in state.cards.values()
    )
    steps: list[str] = []
    due: list[tuple[bool, int, str]] = []
    for card_id, held in state.cards.items():
        card = Card.parse(card_id)
        if held.suspended or not _possible(card_id, situation):
            continue
        made_due = card.rung in FIRST_RUNGS and any(
            state.made_due.get(item, date.max) <= today for item in card.items
        )
        scheduled = held.memory.due < end_of_day and all(spaced(i, card_id) for i in card.items)
        if scheduled and held.memory.phase != "review":
            steps.append(card_id)
        elif made_due or scheduled:
            frequency = max(ranking.frequency.get(item, 0) for item in card.items)
            due.append((not made_due, -frequency, card_id))

    due.sort()
    capped = due[: max(0, settings.review_cap - reviewed_today)]
    return tuple(sorted(steps)) + tuple(card_id for _, _, card_id in capped)


def _passages(
    unknowns: NDArray[np.float64], pack: Pack, read: frozenset[str], settings: Settings
) -> tuple[str, ...]:
    difficulty = np.bincount(pack.appearance_passages, minlength=len(pack.passages))
    order = np.lexsort((difficulty, unknowns))
    unread = np.array([passage not in read for passage in pack.passages], dtype=bool)
    readable = order[unread[order] & (difficulty[order] > 0)]
    chosen: list[int] = readable[: settings.reading_per_day].tolist()
    return tuple(pack.passages[i] for i in chosen)
