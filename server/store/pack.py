import json
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np

from core.pack import Column, GrammarItem, Occurrence, Pack, Passage, Source, Word

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE sources (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, license TEXT NOT NULL, display TEXT NOT NULL
);
CREATE TABLE words (
    id TEXT PRIMARY KEY, spellings TEXT NOT NULL, readings TEXT NOT NULL, glosses TEXT NOT NULL,
    common INTEGER NOT NULL
);
CREATE TABLE passages (
    id TEXT PRIMARY KEY, source TEXT NOT NULL REFERENCES sources,
    position INTEGER NOT NULL, text TEXT NOT NULL
);
CREATE TABLE grammar (
    id TEXT PRIMARY KEY, kind TEXT NOT NULL, prerequisites TEXT NOT NULL, nuance INTEGER NOT NULL
);
CREATE TABLE occurrences (
    passage TEXT NOT NULL REFERENCES passages, item TEXT NOT NULL, spelling TEXT NOT NULL,
    phonetic INTEGER NOT NULL, start INTEGER NOT NULL, end INTEGER NOT NULL,
    probability REAL NOT NULL
);
CREATE INDEX occurrences_by_item ON occurrences (item);
CREATE TABLE translations (passage TEXT PRIMARY KEY REFERENCES passages, text TEXT NOT NULL);
CREATE TABLE senses (word TEXT PRIMARY KEY REFERENCES words, glosses TEXT NOT NULL);
CREATE TABLE pages (
    id TEXT PRIMARY KEY, kind TEXT NOT NULL, name TEXT NOT NULL, written TEXT, label TEXT,
    form TEXT, key TEXT, body TEXT NOT NULL
);
"""


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


def write_pack(
    path: Path,
    meta: Mapping[str, str],
    sources: Iterable[Source],
    words: Iterable[Word],
    grammar: Iterable[GrammarItem],
    passages: Iterable[Passage],
    occurrences: Iterable[Occurrence],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    with sqlite3.connect(path) as db:
        db.executescript(SCHEMA)
        db.executemany("INSERT INTO meta VALUES (?, ?)", meta.items())
        db.executemany(
            "INSERT INTO sources VALUES (?, ?, ?, ?)",
            ((s.id, s.name, s.license, s.display) for s in sources),
        )
        db.executemany(
            "INSERT INTO words VALUES (?, ?, ?, ?, ?)",
            (
                (w.id, _json(w.spellings), _json(w.readings), _json(w.glosses), w.common)
                for w in words
            ),
        )
        db.executemany(
            "INSERT INTO grammar VALUES (?, ?, ?, ?)",
            ((g.id, g.kind, _json(g.prerequisites), g.nuance) for g in grammar),
        )
        db.executemany(
            "INSERT INTO passages VALUES (?, ?, ?, ?)",
            ((p.id, p.source, p.position, p.text) for p in passages),
        )
        db.executemany(
            "INSERT INTO occurrences VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                (o.passage, o.item, o.spelling, o.phonetic, o.start, o.end, o.probability)
                for o in occurrences
            ),
        )
    db.close()


def write_texts(
    path: Path,
    translations: Mapping[str, str],
    senses: Mapping[str, Sequence[Sequence[str]]],
    pages: Iterable[Page],
) -> None:
    """Add what only the learner reads, never core: translations by passage, every sense of
    a word, and grammar pages."""
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


def read_translation(path: Path, passage: str) -> str | None:
    with closing(sqlite3.connect(path)) as db:
        row = db.execute("SELECT text FROM translations WHERE passage = ?", (passage,)).fetchone()
    return None if row is None else row[0]


def read_senses(path: Path, word: str) -> tuple[tuple[str, ...], ...]:
    with closing(sqlite3.connect(path)) as db:
        row = db.execute("SELECT glosses FROM senses WHERE word = ?", (word,)).fetchone()
    return () if row is None else tuple(map(tuple, json.loads(row[0])))


def read_page(path: Path, id: str) -> Page | None:
    with closing(sqlite3.connect(path)) as db:
        row = db.execute("SELECT * FROM pages WHERE id = ?", (id,)).fetchone()
    return None if row is None else Page(*row)


def sample_pack(source: Path, target: Path, every: int) -> None:
    """Copy every n-th passage of a pack, with its occurrences and the items they use."""
    target.unlink(missing_ok=True)
    with closing(sqlite3.connect(target)) as db:
        db.executescript(SCHEMA)
        db.execute("ATTACH DATABASE ? AS source", (str(source),))
        db.executescript(f"""
            INSERT INTO meta SELECT * FROM source.meta;
            INSERT INTO sources SELECT * FROM source.sources;
            INSERT INTO passages SELECT * FROM source.passages WHERE rowid % {every} = 0;
            INSERT INTO occurrences SELECT * FROM source.occurrences
                WHERE passage IN (SELECT id FROM passages);
            INSERT INTO words SELECT * FROM source.words
                WHERE id IN (SELECT item FROM occurrences);
            INSERT INTO grammar SELECT * FROM source.grammar;
            INSERT INTO translations SELECT * FROM source.translations
                WHERE passage IN (SELECT id FROM passages);
            INSERT INTO senses SELECT * FROM source.senses WHERE word IN (SELECT id FROM words);
            INSERT INTO pages SELECT * FROM source.pages;
        """)
        db.commit()
        db.execute("DETACH DATABASE source")
        db.execute("VACUUM")


def read_words(path: Path) -> list[Word]:
    with closing(sqlite3.connect(path)) as db:
        rows = db.execute("SELECT id, spellings, readings, glosses, common FROM words").fetchall()
    return [
        Word(
            id,
            tuple(json.loads(spellings)),
            tuple(json.loads(readings)),
            tuple(json.loads(glosses)),
            bool(common),
        )
        for id, spellings, readings, glosses, common in rows
    ]


def read_passages(path: Path) -> list[Passage]:
    with closing(sqlite3.connect(path)) as db:
        rows = db.execute("SELECT id, source, position, text FROM passages ORDER BY rowid")
        return [Passage(id, source, position, text) for id, source, position, text in rows]


def read_pack(path: Path) -> Pack:
    with closing(sqlite3.connect(path)) as db:
        sources = [row[0] for row in db.execute("SELECT id FROM sources ORDER BY id")]
        passages = db.execute("SELECT id, source FROM passages ORDER BY rowid").fetchall()
        appearances = db.execute(
            "SELECT passage, item, CASE WHEN phonetic THEN NULL ELSE spelling END AS written,"
            " MAX(probability) FROM occurrences GROUP BY passage, item, written"
        ).fetchall()
        grammar = [
            GrammarItem(id, kind, tuple(json.loads(prerequisites)), bool(nuance))
            for id, kind, prerequisites, nuance in db.execute("SELECT * FROM grammar")
        ]

    source_index = {source: i for i, source in enumerate(sources)}
    passage_index = {passage: i for i, (passage, _) in enumerate(passages)}
    column_index: dict[Column, int] = {}
    appearance_columns = [
        column_index.setdefault(Column(item, spelling), len(column_index))
        for _, item, spelling, _ in appearances
    ]

    return Pack(
        passages=tuple(passage for passage, _ in passages),
        sources=tuple(sources),
        passage_sources=np.array([source_index[source] for _, source in passages], dtype=np.int32),
        columns=tuple(column_index),
        appearance_passages=np.array(
            [passage_index[passage] for passage, _, _, _ in appearances], dtype=np.int32
        ),
        appearance_columns=np.array(appearance_columns, dtype=np.int32),
        appearance_probabilities=np.array([p for *_, p in appearances], dtype=np.float64),
        grammar={item.id: item for item in grammar},
    )


def _json(values: tuple[str, ...]) -> str:
    return json.dumps(values, ensure_ascii=False)
