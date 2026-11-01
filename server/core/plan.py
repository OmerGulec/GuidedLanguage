from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import numpy as np
from numpy.typing import NDArray

from core.candidates import LADDER_OF, Ranking, offers, showable
from core.cards import FIRST_RUNGS, LADDERS, RUNGS, Card, Goal, ladder
from core.days import next_boundary, study_day
from core.events import Modality
from core.pack import Pack
from core.settings import Settings
from core.state import State, starting

LISTENING_GOALS: frozenset[Goal] = frozenset({"listener", "complete"})


@dataclass(frozen=True, slots=True)
class Situation:
    sound: bool = True
    keyboard: bool = True


@dataclass(frozen=True, slots=True)
class Plan:
    reviews: tuple[str, ...]
    # Learning steps due later in the study day: shown after everything else.
    later: tuple[str, ...]
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

    # New items spend the new budget; rungs that unlocked get an equal allowance of their own,
    # so a goal with more rungs adds cards without slowing the pace of new words. New grammar
    # also spends the grammar cap.
    today = study_day(now, settings)
    learned_today = [
        Card.parse(card) for card, held in state.cards.items() if held.learned == today
    ]
    shown_today = [
        item
        for item, at in state.introduced.items()
        if _system(item, ranking) and study_day(at, settings) == today
    ]
    started = Counter(card.rung in FIRST_RUNGS for card in learned_today)
    later_rungs = any(len(ladder(kind, goal)) > 1 for kind in LADDERS)
    allowance = {
        True: max(0, settings.new_budget - started[True] - len(shown_today) - len(reteach)),
        False: max(0, settings.new_budget - started[False]) if later_rungs else 0,
    }
    grammar_started = sum(
        card.rung in FIRST_RUNGS and card.items[0] in ranking.grammar for card in learned_today
    )
    grammar_left = max(0, settings.grammar_cap - grammar_started - len(shown_today))
    new: list[str] = []
    for offer in offers(state, ranking, goal):
        if allowance[True] == 0 and allowance[False] == 0:
            break
        system = _system(offer, ranking)
        card = None if system else Card.parse(offer)
        first = card is None or card.rung in FIRST_RUNGS
        grammar = first and (card is None or card.items[0] in ranking.grammar)
        if allowance[first] == 0 or (grammar and grammar_left == 0):
            continue
        if card is None or _possible(offer, situation):
            new.append(offer)
            allowance[first] -= 1
            grammar_left -= grammar

    modalities: list[Modality] = ["reading"]
    if goal in LISTENING_GOALS and situation.sound:
        modalities.append("listening")

    reviews, later = _reviews(state, ranking, goal, situation, settings, now)
    return Plan(
        reviews=reviews,
        later=later,
        reteach=tuple(reteach),
        new=tuple(new),
        passages={m: _passages(unknowns[m], pack, state.read[m], settings) for m in modalities},
    )


def _system(offer: str, ranking: Ranking) -> bool:
    """A system is offered by its item id, having no cards."""
    item = ranking.grammar.get(offer)
    return item is not None and item.kind == "system"


def _first_card(item: str, ranking: Ranking) -> str | None:
    grammar = ranking.grammar.get(item)
    if grammar is None:
        return Card((item,), ranking.spellings.get(item), LADDERS["word"][0].name).id
    if grammar.kind == "system":
        return None
    return Card((item,), None, LADDERS[LADDER_OF[grammar.kind]][0].name).id


def _possible(card: str, situation: Situation) -> bool:
    rung = RUNGS[Card.parse(card).rung]
    return (situation.sound or not rung.needs_sound) and (
        situation.keyboard or not rung.needs_keyboard
    )


def _reviews(
    state: State,
    ranking: Ranking,
    goal: Goal,
    situation: Situation,
    settings: Settings,
    now: datetime,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Cards due now, then learning steps due later in the study day."""
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
    steps: list[tuple[datetime, str]] = []
    due: list[tuple[bool, float, str]] = []
    for card_id, held in state.cards.items():
        card = Card.parse(card_id)
        # Cards outside the goal, such as imported ones, are kept but not reviewed (013). Cards
        # the situation rules out, or with no passage to show, wait.
        if (
            held.suspended
            or goal not in RUNGS[card.rung].goals
            or not _possible(card_id, situation)
            or not all(showable(item, ranking) for item in card.items)
        ):
            continue
        made_due = card.rung in FIRST_RUNGS and any(
            state.made_due.get(item, date.max) <= today for item in card.items
        )
        scheduled = held.memory.due < end_of_day and all(spaced(i, card_id) for i in card.items)
        if scheduled and held.memory.phase != "review":
            steps.append((held.memory.due, card_id))
        elif made_due or scheduled:
            frequency = max(ranking.frequency.get(item, 0) for item in card.items)
            due.append((not made_due, -frequency, card_id))

    # A marked item's first card comes due from its starting memory (013, 014). It comes the
    # next study day if a lookup made it due or a mark it builds on was withdrawn.
    first_held = {
        item
        for card in map(Card.parse, state.cards)
        if card.rung in FIRST_RUNGS
        for item in card.items
    }
    for item, mark in state.marks.items():
        card_id = _first_card(item, ranking)
        if (
            mark.status != "known"
            or card_id is None
            or item in first_held
            or not showable(item, ranking)
        ):
            continue
        grammar = ranking.grammar.get(item)
        prerequisites = () if grammar is None else grammar.prerequisites
        made_due = state.made_due.get(item, date.max) <= today or any(
            state.withdrawn.get(p, date.max) < today for p in prerequisites
        )
        scheduled = starting(item, mark, settings).memory.due < end_of_day
        if made_due or scheduled:
            due.append((not made_due, -ranking.frequency.get(item, 0), card_id))

    # A learning step comes once due, so a just-learned card returns with other cards between.
    # One due later in the day waits until the rest is done, then comes early rather than
    # leaving the learner waiting.
    steps.sort()
    due.sort()
    capped = due[: max(0, settings.review_cap - reviewed_today)]
    reviews = tuple(card for at, card in steps if at <= now) + tuple(c for _, _, c in capped)
    return reviews, tuple(card for at, card in steps if at > now)


def _passages(
    unknowns: NDArray[np.float64], pack: Pack, read: frozenset[str], settings: Settings
) -> tuple[str, ...]:
    difficulty = np.bincount(pack.appearance_passages, minlength=len(pack.passages))
    order = np.lexsort((difficulty, unknowns))
    unread = np.array([passage not in read for passage in pack.passages], dtype=bool)
    readable = order[unread[order] & (difficulty[order] > 0)]
    chosen: list[int] = readable[: settings.reading_per_day].tolist()
    return tuple(pack.passages[i] for i in chosen)
