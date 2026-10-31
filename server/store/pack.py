import json
import sqlite3
from collections.abc import Iterable, Mapping
from pathlib import Path

from core.pack import Occurrence, Passage, Source, Word

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


def _json(values: tuple[str, ...]) -> str:
    return json.dumps(values, ensure_ascii=False)
