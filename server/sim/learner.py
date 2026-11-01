import random
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

import numpy as np
from numpy.typing import NDArray

from core.candidates import Ranking
from core.cards import Card, Goal
from core.events import Event, Introduced, LookedUp, Marked, Modality, Payload, Read, Reviewed
from core.pack import Pack
from core.plan import Situation, plan
from core.settings import Settings
from core.state import EMPTY, advance
from core.unknowns import unknowns
from core.values import values

# Simulated memory forgets exponentially, unlike the scheduler's power curve, so the simulator
# never checks the scheduler against a copy of itself.
FIRST_HALF_LIFE_DAYS = 5.0
KNOWN_HALF_LIFE_DAYS = 200.0
HALF_LIFE_SPREAD = 0.5
# A pass multiplies the half-life by 1 + SPACING_GAIN * (1 - recall chance): little for a
# repetition a minute later, about 2.5 for a review at the scheduler's 90% target.
SPACING_GAIN = 15.0
SHRINK_ON_FAIL = 0.5
FIRST_ANSWER_PASS = 0.8
LOOKUP_CHANCE = 0.6

STUDY_HOUR = 20
ANSWER_TIME = timedelta(seconds=20)
SESSION_GAP = timedelta(minutes=15)
SESSIONS_PER_DAY = 3
MODALITIES: tuple[Modality, ...] = ("reading", "listening")


@dataclass(frozen=True, slots=True)
class Learner:
    name: str
    seed: int
    goal: Goal = "reader"
    situation: Situation = field(default_factory=Situation)


@dataclass(frozen=True, slots=True)
class DayRecord:
    day: date
    reviews: int
    failed: int
    new: int


@dataclass(slots=True)
class _Trace:
    half_life: float
    seen: datetime


class Simulation:
    def __init__(
        self, learner: Learner, pack: Pack, ranking: Ranking, settings: Settings, start: date
    ) -> None:
        self.learner = learner
        self.pack = pack
        self.ranking = ranking
        self.settings = settings
        self.day = start
        self.events: list[Event] = []
        self.state = EMPTY
        self.days: list[DayRecord] = []
        self._random = random.Random(learner.seed)
        self._traces: dict[str, _Trace] = {}
        self._known: dict[str, _Trace] = {}
        self._passage_index = {passage: i for i, passage in enumerate(pack.passages)}
        self._passage_items: list[set[str]] = [set() for _ in pack.passages]
        passages: list[int] = pack.appearance_passages.tolist()
        columns: list[int] = pack.appearance_columns.tolist()
        for passage, column in zip(passages, columns, strict=True):
            self._passage_items[passage].add(pack.columns[column].item)

    def import_known(self, items: Iterable[str]) -> None:
        at = self._study_time()
        marks: list[Payload] = []
        for item in items:
            self._known[item] = _Trace(self._half_life(item, KNOWN_HALF_LIFE_DAYS), at)
            marks.append(Marked(item, "known", "import"))
        self._apply(at, marks)

    def run(self, days: int) -> None:
        for _ in range(days):
            self._study_day()
            self.day += timedelta(days=1)

    def _study_day(self) -> None:
        now = self._study_time()
        unknown: dict[Modality, NDArray[np.float64]] = {
            m: unknowns(values(self.state, self.pack, self.settings, now, m), self.pack)
            for m in MODALITIES
        }
        reviews = failed = new = 0

        for session in range(SESSIONS_PER_DAY):
            today = plan(
                self.state,
                unknown,
                self.pack,
                self.ranking,
                self.learner.goal,
                self.learner.situation,
                self.settings,
                now,
            )
            payloads: list[Payload] = [Introduced(item, "reteach") for item in today.reteach]
            for card in today.reviews:
                passed = self._answer(card, now)
                payloads.append(Reviewed(card, passed, "self"))
                reviews, failed = reviews + 1, failed + (not passed)
            for offer in today.new:
                new += 1
                # A system has no cards: it is offered by its item id and only shown.
                if offer in self.pack.grammar:
                    payloads.append(Introduced(offer, "new"))
                    continue
                for item in Card.parse(offer).items:
                    if item not in self.state.introduced:
                        payloads.append(Introduced(item, "new"))
                payloads.append(Reviewed(offer, self._answer(offer, now), "self"))
            if session == 0:
                for modality, passages in today.passages.items():
                    payloads.extend(self._read(passages, modality, now))
            if not payloads:
                break
            now = self._apply(now, payloads) + SESSION_GAP

        self.days.append(DayRecord(self.day, reviews, failed, new))

    def _answer(self, card: str, at: datetime) -> bool:
        trace = self._traces.get(card)
        if trace is None:
            known = self._first_rung_known(card)
            if known is None:
                self._traces[card] = _Trace(self._half_life(card, FIRST_HALF_LIFE_DAYS), at)
                return self._random.random() < FIRST_ANSWER_PASS
            trace = self._traces[card] = _Trace(known.half_life, known.seen)

        chance = self._chance(trace, at)
        passed = self._random.random() < chance
        if passed:
            trace.half_life *= 1 + SPACING_GAIN * (1 - chance)
        else:
            trace.half_life *= SHRINK_ON_FAIL
        trace.seen = at
        return passed

    def _read(self, passages: Iterable[str], modality: Modality, at: datetime) -> list[Payload]:
        payloads: list[Payload] = []
        for passage in passages:
            payloads.append(Read(passage, modality))
            for item in sorted(self._passage_items[self._passage_index[passage]]):
                understood = self._random.random() < self._understanding(item, at)
                if not understood and self._random.random() < LOOKUP_CHANCE:
                    payloads.append(LookedUp(item, passage, surface="", context=""))
        return payloads

    def _understanding(self, item: str, at: datetime) -> float:
        traces = [t for card, t in self._traces.items() if item in Card.parse(card).items]
        if item in self._known:
            traces.append(self._known[item])
        return max((self._chance(t, at) for t in traces), default=0.0)

    def _first_rung_known(self, card: str) -> _Trace | None:
        parsed = Card.parse(card)
        if parsed.rung != "recognize":
            return None
        return next((self._known[i] for i in parsed.items if i in self._known), None)

    def _half_life(self, key: str, typical: float) -> float:
        spread = random.Random(f"{self.learner.seed}:{key}").gauss(0, HALF_LIFE_SPREAD)
        return typical * 2**spread

    @staticmethod
    def _chance(trace: _Trace, at: datetime) -> float:
        elapsed = (at - trace.seen) / timedelta(days=1)
        return 2 ** (-elapsed / trace.half_life)

    def _study_time(self) -> datetime:
        return datetime.combine(self.day, time(STUDY_HOUR), tzinfo=self.settings.zone)

    def _apply(self, at: datetime, payloads: list[Payload]) -> datetime:
        events: list[Event] = []
        for payload in payloads:
            events.append(Event(f"{self.learner.name}-{len(self.events)}", at, "sim", payload))
            self.events.append(events[-1])
            at += ANSWER_TIME
        self.state = advance(self.state, events, self.settings)
        return at
