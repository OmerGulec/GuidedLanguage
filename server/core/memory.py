from dataclasses import dataclass
from datetime import UTC, datetime
from functools import cache
from typing import Literal

import fsrs

from core.settings import Settings

type Phase = Literal["learning", "review", "relearning"]

_PHASES: dict[fsrs.State, Phase] = {
    fsrs.State.Learning: "learning",
    fsrs.State.Review: "review",
    fsrs.State.Relearning: "relearning",
}
_STATES = {phase: state for state, phase in _PHASES.items()}


@dataclass(frozen=True, slots=True)
class Memory:
    stability: float
    difficulty: float
    phase: Phase
    step: int | None
    due: datetime
    last_review: datetime


def review(memory: Memory | None, passed: bool, at: datetime, settings: Settings) -> Memory:
    rating = fsrs.Rating.Good if passed else fsrs.Rating.Again
    card, _ = _scheduler(settings).review_card(_card(memory), rating, at.astimezone(UTC))
    assert card.stability is not None and card.difficulty is not None
    return Memory(
        stability=card.stability,
        difficulty=card.difficulty,
        phase=_PHASES[card.state],
        step=card.step,
        due=card.due,
        last_review=at.astimezone(UTC),
    )


def recall(memory: Memory, at: datetime, settings: Settings) -> float:
    return _scheduler(settings).get_card_retrievability(_card(memory), at.astimezone(UTC))


@cache
def _scheduler(settings: Settings) -> fsrs.Scheduler:
    # Fuzzing would draw from an unseeded random source and make replay non-deterministic.
    return fsrs.Scheduler(
        parameters=settings.scheduler_parameters,
        desired_retention=settings.retention,
        enable_fuzzing=False,
    )


def _card(memory: Memory | None) -> fsrs.Card:
    if memory is None:
        return fsrs.Card(card_id=0)
    return fsrs.Card(
        card_id=0,
        state=_STATES[memory.phase],
        step=memory.step,
        stability=memory.stability,
        difficulty=memory.difficulty,
        due=memory.due,
        last_review=memory.last_review,
    )
