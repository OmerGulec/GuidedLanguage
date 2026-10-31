"""A learner's Renshuu history, fetched through its API and replayed as our events (013)."""

import os
import sys
import urllib.request
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from core.cards import Card
from core.events import Event, Introduced, Reviewed
from core.pack import Word
from core.settings import Settings
from core.state import derive
from core.unknowns import unknowns
from core.values import values
from integrations.wordlist import match
from store.pack import read_pack, read_words
from store.paths import DATA, PACK

API = "https://api.renshuu.org/v1"
KEY_VARIABLE = "read_only_renshuu"
TERM_TYPES = ("vocab", "kanji", "grammar")
DUMP = DATA / "renshuu"
ORIGIN = "renshuu"
# Renshuu records the day of an answer, not the time. Noon UTC falls on the same study day in
# most time zones.
ANSWER_HOUR = 12

# Renshuu's study vectors by the rung they exercise, and whether in the word's kanji spelling.
# Kana > Kanji and Writing test writing, which no rung covers; their history stays in the dump.
VECTOR_RUNGS: dict[str, tuple[str, bool]] = {
    "Kanji > Kana": ("recognize", True),
    "Kanji > Meaning": ("recognize", True),
    "Kana > Meaning": ("recognize", False),
    "Listening": ("listen", False),
    "Accent": ("pitch", False),
    "Meaning > Kana": ("cloze", False),
    "Meaning > Kanji": ("cloze", False),
}


class _Answer(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    day: str = Field(alias="date")
    correct: Literal["yes", "no"]


class _Vector(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    answers: tuple[_Answer, ...] = Field(default=(), alias="study_history")


class _Progress(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    introduced: str | None = Field(default=None, alias="introduced_date")
    vectors: dict[str, _Vector] = Field(default_factory=dict[str, _Vector], alias="study_vectors")


class RenshuuWord(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    entry: str | None = Field(alias="edict_ent")
    spelling: str = Field(default="", alias="kanji_full")
    reading: str = Field(alias="hiragana_full")
    progress: _Progress | None = Field(default=None, alias="user_data")


class _Contents(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    pages: int = Field(alias="total_pg")
    words: tuple[RenshuuWord, ...] = Field(default=(), alias="terms")


class _Page(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    contents: _Contents


class _Pages(BaseModel):
    pages: int = Field(alias="total_pg")


class _PageCount(BaseModel):
    contents: _Pages


@dataclass(frozen=True, slots=True)
class Imported:
    events: list[Event]
    # Renshuu words whose dictionary entry the pack does not have.
    unmatched: list[str]


def fetch(key: str, dump: Path) -> None:
    """Save every page of the learner's studied terms, with full answer history."""
    dump.mkdir(parents=True, exist_ok=True)
    for term_type in TERM_TYPES:
        page, pages = 1, 1
        while page <= pages:
            url = f"{API}/list/all/{term_type}?pg={page}&history=full"
            request = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
            with urllib.request.urlopen(request) as response:
                body: bytes = response.read()
            (dump / f"{term_type}-{page}.json").write_bytes(body)
            pages = _PageCount.model_validate_json(body).contents.pages
            page += 1


def read_words_dump(dump: Path) -> list[RenshuuWord]:
    pages = sorted(dump.glob("vocab-*.json"))
    return [w for p in pages for w in _Page.model_validate_json(p.read_bytes()).contents.words]


def replay(words: Iterable[RenshuuWord], known: Mapping[str, Word]) -> Imported:
    """Each word's introduction and, per card and day, one review that fails if any answer
    that day was wrong. Event ids are fixed, so importing again adds nothing."""
    events: list[Event] = []
    unmatched: list[str] = []
    for renshuu_word in words:
        item = _item(renshuu_word, known)
        if item is None:
            unmatched.append(renshuu_word.spelling or renshuu_word.reading)
            continue
        word = known[item]
        progress = renshuu_word.progress
        if progress is None:
            continue

        if progress.introduced:
            introduced = Introduced(item, "import")
            events.append(Event(f"{ORIGIN}/{item}", _at(progress.introduced), ORIGIN, introduced))

        spelling = _spelling(renshuu_word, word)
        passed: dict[tuple[str, str], bool] = {}
        for name, vector in progress.vectors.items():
            if name not in VECTOR_RUNGS:
                continue
            rung, in_kanji = VECTOR_RUNGS[name]
            card = Card((item,), spelling if in_kanji else None, rung).id
            for answer in vector.answers:
                key = (card, answer.day)
                passed[key] = passed.get(key, True) and answer.correct == "yes"

        for (card, day), result in passed.items():
            review = Reviewed(card, result, "import")
            events.append(Event(f"{ORIGIN}/{card}/{day}", _at(day), ORIGIN, review))
    return Imported(events, unmatched)


def _item(renshuu_word: RenshuuWord, known: Mapping[str, Word]) -> str | None:
    if renshuu_word.entry is not None:
        item = f"w:{renshuu_word.entry}"
        return item if item in known else None
    # Renshuu files a few する verbs as words of their own; the dictionary has the noun.
    wanted = [(renshuu_word.spelling or renshuu_word.reading, renshuu_word.reading)]
    found = match(wanted, known.values(), frequency={})
    ids = [*found.known.values(), *(ids[0] for ids in found.guessed.values())]
    return ids[0] if ids else None


def _spelling(renshuu_word: RenshuuWord, word: Word) -> str | None:
    """The kanji spelling Renshuu showed, if the dictionary has it; kana words have none."""
    if renshuu_word.spelling in word.spellings:
        return renshuu_word.spelling
    return word.spellings[0] if word.spellings else None


def _at(day: str) -> datetime:
    year, month, number = map(int, day.split("/"))
    return datetime(year, month, number, ANSWER_HOUR, tzinfo=UTC)


def report(dump: Path) -> None:
    pack, words = read_pack(PACK), read_words(PACK)
    renshuu_words = read_words_dump(dump)
    imported = replay(renshuu_words, {w.id: w for w in words})
    print(f"{len(renshuu_words)} words, {len(imported.unmatched)} not in the dictionary")
    if imported.unmatched:
        print("  not found:", ", ".join(imported.unmatched))

    reviews = [e.payload for e in imported.events if isinstance(e.payload, Reviewed)]
    rungs = Counter(Card.parse(review.card).rung for review in reviews)
    print(f"{len(reviews)} reviews by rung:", ", ".join(f"{r} {n}" for r, n in rungs.most_common()))

    settings = Settings()
    state = derive(imported.events, settings)
    now = datetime.now(UTC)
    overdue = sum(card.memory.due < now for card in state.cards.values())
    print(f"{len(state.cards)} cards, {overdue} due now")

    per_passage = unknowns(values(state, pack, settings, now, "reading"), pack)
    print(f"passages fully known: {np.mean(per_passage < 0.5):.1%}")
    print(f"passages with one unknown: {np.mean((per_passage >= 0.5) & (per_passage < 1.5)):.1%}")


if __name__ == "__main__":
    match sys.argv[1:]:
        case ["fetch"]:
            fetch(os.environ[KEY_VARIABLE], DUMP)
        case ["report"]:
            report(DUMP)
        case _:
            sys.exit("usage: python -m integrations.renshuu fetch|report")
