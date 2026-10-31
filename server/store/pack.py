import json
import sqlite3
from collections.abc import Iterable, Mapping
from contextlib import closing
from pathlib import Path

import numpy as np

from core.pack import Column, Occurrence, Pack, Passage, Source, Word

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE sources (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, license TEXT NOT NULL, display TEXT NOT NULL
);
CREATE TABLE words (
    id TEXT PRIMARY KEY, spellings TEXT NOT NULL, readings TEXT NOT NULL, glosses TEXT NOT NULL
);
CREATE TABLE passages (
    id TEXT PRIMARY KEY, source TEXT NOT NULL REFERENCES sources,
    position INTEGER NOT NULL, text TEXT NOT NULL
);
CREATE TABLE occurrences (
    passage TEXT NOT NULL REFERENCES passages, item TEXT NOT NULL, spelling TEXT NOT NULL,
    phonetic INTEGER NOT NULL, start INTEGER NOT NULL, end INTEGER NOT NULL
);
CREATE INDEX occurrences_by_item ON occurrences (item);
"""


def write_pack(
    path: Path,
    meta: Mapping[str, str],
    sources: Iterable[Source],
    words: Iterable[Word],
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
            "INSERT INTO words VALUES (?, ?, ?, ?)",
            ((w.id, _json(w.spellings), _json(w.readings), _json(w.glosses)) for w in words),
        )
        db.executemany(
            "INSERT INTO passages VALUES (?, ?, ?, ?)",
            ((p.id, p.source, p.position, p.text) for p in passages),
        )
        db.executemany(
            "INSERT INTO occurrences VALUES (?, ?, ?, ?, ?, ?)",
            ((o.passage, o.item, o.spelling, o.phonetic, o.start, o.end) for o in occurrences),
        )
    db.close()


def read_pack(path: Path) -> Pack:
    with closing(sqlite3.connect(path)) as db:
        sources = [row[0] for row in db.execute("SELECT id FROM sources ORDER BY id")]
        passages = db.execute("SELECT id, source FROM passages ORDER BY rowid").fetchall()
        appearances = db.execute(
            "SELECT DISTINCT passage, item, CASE WHEN phonetic THEN NULL ELSE spelling END"
            " FROM occurrences"
        ).fetchall()

    source_index = {source: i for i, source in enumerate(sources)}
    passage_index = {passage: i for i, (passage, _) in enumerate(passages)}
    column_index: dict[Column, int] = {}
    appearance_columns = [
        column_index.setdefault(Column(item, spelling), len(column_index))
        for _, item, spelling in appearances
    ]

    return Pack(
        passages=tuple(passage for passage, _ in passages),
        sources=tuple(sources),
        passage_sources=np.array([source_index[source] for _, source in passages], dtype=np.int32),
        columns=tuple(column_index),
        appearance_passages=np.array(
            [passage_index[passage] for passage, _, _ in appearances], dtype=np.int32
        ),
        appearance_columns=np.array(appearance_columns, dtype=np.int32),
    )


def _json(values: tuple[str, ...]) -> str:
    return json.dumps(values, ensure_ascii=False)
