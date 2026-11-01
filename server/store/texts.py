"""What the learner reads from a pack and core never does: translations, every sense of a word,
grammar pages, and passages with their items for display."""

import json
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from core.pack import Occurrence, Passage, Word


@dataclass(frozen=True, slots=True)
class Page:
    """A grammar item's page, or a form page (010)."""

    id: str
    kind: Literal["form", "use", "formation", "system"]
    name: str
    written: str | None
    label: str | None
    form: str | None
    key: str | None
    body: str


def write_texts(
    path: Path,
    translations: Mapping[str, str],
    senses: Mapping[str, Sequence[Sequence[str]]],
    pages: Iterable[Page],
) -> None:
    with closing(sqlite3.connect(path)) as db:
        db.executemany("INSERT INTO translations VALUES (?, ?)", translations.items())
        db.executemany(
            "INSERT INTO senses VALUES (?, ?)",
            ((word, json.dumps(glosses, ensure_ascii=False)) for word, glosses in senses.items()),
        )
        db.executemany(
            "INSERT INTO pages VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ((p.id, p.kind, p.name, p.written, p.label, p.form, p.key, p.body) for p in pages),
        )
        db.commit()


def open_texts(path: Path) -> sqlite3.Connection:
    """One read-only connection, shared by the server's threads."""
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)


def read_translation(db: sqlite3.Connection, passage: str) -> str | None:
    row = db.execute("SELECT text FROM translations WHERE passage = ?", (passage,)).fetchone()
    return None if row is None else row[0]


def read_senses(db: sqlite3.Connection, word: str) -> tuple[tuple[str, ...], ...]:
    row = db.execute("SELECT glosses FROM senses WHERE word = ?", (word,)).fetchone()
    return () if row is None else tuple(map(tuple, json.loads(row[0])))


def read_page(db: sqlite3.Connection, id: str) -> Page | None:
    row = db.execute("SELECT * FROM pages WHERE id = ?", (id,)).fetchone()
    return None if row is None else Page(*row)


def read_word(db: sqlite3.Connection, id: str) -> Word | None:
    row = db.execute(
        "SELECT spellings, readings, glosses, common FROM words WHERE id = ?", (id,)
    ).fetchone()
    if row is None:
        return None
    spellings, readings, glosses, common = row
    return Word(
        id,
        tuple(json.loads(spellings)),
        tuple(json.loads(readings)),
        tuple(json.loads(glosses)),
        bool(common),
    )


def read_passage(db: sqlite3.Connection, id: str) -> Passage | None:
    row = db.execute("SELECT * FROM passages WHERE id = ?", (id,)).fetchone()
    return None if row is None else Passage(*row)


def read_occurrences(db: sqlite3.Connection, passage: str) -> list[Occurrence]:
    """A passage's occurrences in reading order, every use a grammar form may have among them."""
    rows = db.execute(
        "SELECT * FROM occurrences WHERE passage = ? ORDER BY start, end", (passage,)
    ).fetchall()
    return [Occurrence(p, i, s, bool(ph), start, end, pr) for p, i, s, ph, start, end, pr in rows]
