"""The pack as the API serves it: core's view for planning, and what the learner reads."""

import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel

from core.candidates import Ranking, ranking
from core.pack import Column, Pack
from core.passages import SETTLED
from core.settings import Settings
from core.state import State
from store.pack import read_eligible, read_pack
from store.texts import (
    open_texts,
    read_occurrences,
    read_page,
    read_passage,
    read_senses,
    read_translation,
    read_word,
)

type Status = Literal["known", "fading", "unknown"]


class WordView(BaseModel):
    kind: Literal["word"] = "word"
    id: str
    spellings: list[str]
    readings: list[str]
    # The main meaning, which cards are graded on (004), then the other senses.
    meaning: list[str]
    senses: list[list[str]]


class FormView(BaseModel):
    name: str
    written: str | None
    body: str


class GrammarView(BaseModel):
    kind: Literal["grammar"] = "grammar"
    id: str
    grammar: Literal["use", "formation", "system"]
    name: str
    written: str | None
    key: str | None
    lesson: str
    form: FormView | None


class Span(BaseModel):
    """An item where it appears in a passage, with what a tap on it shows."""

    start: int
    end: int
    status: Status
    # A word, or grammar: the use where settled, otherwise the uses the learner was taught.
    items: list[str]


class PassageView(BaseModel):
    id: str
    text: str
    translation: str | None
    source: str
    position: int
    spans: list[Span]
    items: dict[str, WordView | GrammarView]


@dataclass(frozen=True, slots=True, eq=False)
class Library:
    db: sqlite3.Connection
    pack: Pack
    ranking: Ranking
    eligible: NDArray[np.bool_]
    columns: dict[Column, int]


def load_library(path: Path, settings: Settings) -> Library:
    pack, eligible = read_pack(path), read_eligible(path)
    columns = {column: i for i, column in enumerate(pack.columns)}
    return Library(open_texts(path), pack, ranking(pack, settings, eligible), eligible, columns)


def word_view(library: Library, id: str) -> WordView | None:
    word = read_word(library.db, id)
    if word is None:
        return None
    senses = read_senses(library.db, id)
    return WordView(
        id=id,
        spellings=list(word.spellings),
        readings=list(word.readings),
        meaning=list(word.glosses),
        senses=[list(sense) for sense in senses[1:]],
    )


def grammar_view(library: Library, id: str) -> GrammarView | None:
    page = read_page(library.db, id)
    if page is None or page.kind == "form":
        return None
    form = None if page.form is None else read_page(library.db, page.form)
    return GrammarView(
        id=id,
        grammar=page.kind,
        name=page.name,
        written=page.written,
        key=page.key,
        lesson=page.body,
        form=None
        if form is None
        else FormView(name=form.name, written=form.written, body=form.body),
    )


def item_view(library: Library, id: str) -> WordView | GrammarView | None:
    return grammar_view(library, id) if id in library.pack.grammar else word_view(library, id)


def passage_view(
    library: Library, id: str, state: State, values: NDArray[np.float64]
) -> PassageView | None:
    """A passage with every item in it, so a tap needs no further request. Values are the
    learner's, for reading."""
    passage = read_passage(library.db, id)
    if passage is None:
        return None

    forms: dict[tuple[int, int], list[tuple[str, float, str | None]]] = defaultdict(list)
    for o in read_occurrences(library.db, id):
        forms[o.start, o.end].append((o.item, o.probability, None if o.phonetic else o.spelling))
    known = {item for item, mark in state.marks.items() if mark.status == "known"}
    taught = state.introduced.keys() | known
    spans: list[Span] = []
    for (start, end), found in sorted(forms.items()):
        settled = [item for item, p, _ in found if p >= SETTLED]
        shown = settled or [item for item, _, _ in found if item in taught]
        value = min(_value(library, values, item, spelling) for item, _, spelling in found)
        spans.append(Span(start=start, end=end, status=_status(value), items=shown))

    views = {item: item_view(library, item) for span in spans for item in span.items}
    return PassageView(
        id=id,
        text=passage.text,
        translation=read_translation(library.db, id),
        source=passage.source,
        position=passage.position,
        spans=spans,
        items={item: view for item, view in views.items() if view is not None},
    )


def _value(library: Library, values: NDArray[np.float64], item: str, spelling: str | None) -> float:
    column = library.columns.get(Column(item, spelling))
    return 0.0 if column is None else float(values[column])


def _status(value: float) -> Status:
    if value >= 1.0:
        return "known"
    return "unknown" if value == 0.0 else "fading"
