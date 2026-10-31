import sys
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np

from core.candidates import ranking
from core.events import Event, Marked
from core.pack import Word
from core.settings import Settings
from core.state import derive
from core.unknowns import unknowns
from core.values import values
from langs.ja.analyser import hiragana
from langs.ja.content import rows
from store.pack import read_pack, read_words
from store.paths import PACK

SHOWN = 15


@dataclass(frozen=True, slots=True)
class Matches:
    known: dict[str, str]
    # Words that fit several entries: the entry most common in the library comes first.
    guessed: dict[str, tuple[str, ...]]
    missing: list[str]


def read_word_list(path: Path) -> list[tuple[str, str | None]]:
    return [(row[0], row[1] if len(row) > 1 and row[1] else None) for row in rows(path)]


def match(
    wanted: Iterable[tuple[str, str | None]], words: Iterable[Word], frequency: Mapping[str, int]
) -> Matches:
    by_form: dict[str, list[Word]] = defaultdict(list)
    for word in words:
        for form in {*word.spellings, *map(hiragana, word.readings)}:
            by_form[form].append(word)

    known: dict[str, str] = {}
    guessed: dict[str, tuple[str, ...]] = {}
    missing: list[str] = []
    for spelling, reading in wanted:
        fitting = [
            w
            for w in by_form.get(spelling, []) + by_form.get(hiragana(spelling), [])
            if reading is None or hiragana(reading) in map(hiragana, w.readings)
        ]
        ids = sorted({w.id for w in fitting}, key=lambda i: (-frequency.get(i, 0), i))
        line = spelling if reading is None else f"{spelling} ({reading})"
        if len(ids) == 1:
            known[line] = ids[0]
        elif ids:
            guessed[line] = tuple(ids)
        else:
            missing.append(line)
    return Matches(known, guessed, missing)


def report(path: Path) -> None:
    pack, words = read_pack(PACK), read_words(PACK)
    pack_ranking = ranking(pack)
    matches = match(read_word_list(path), words, pack_ranking.frequency)
    labels = {w.id: w.spellings[0] if w.spellings else w.readings[0] for w in words}

    known, guessed, missing = len(matches.known), len(matches.guessed), len(matches.missing)
    print(f"known {known}, guessed {guessed}, missing {missing}")
    for line, ids in list(matches.guessed.items())[:SHOWN]:
        print(f"  guessed {line}: {labels[ids[0]]}, not {', '.join(labels[i] for i in ids[1:])}")
    if matches.missing:
        print("  missing:", ", ".join(matches.missing[:SHOWN]))

    imported_at = datetime.now(UTC)
    items = {*matches.known.values(), *(ids[0] for ids in matches.guessed.values())}
    marks = [
        Event(f"import-{i}", imported_at, "import", Marked(i, "known", "import")) for i in items
    ]
    settings = Settings()
    state = derive(marks, settings)
    tomorrow = imported_at + timedelta(days=1)
    per_passage = unknowns(values(state, pack, settings, tomorrow, "reading"), pack)
    print(f"passages fully known: {np.mean(per_passage < 0.5):.1%}")
    print(f"passages with one unknown: {np.mean((per_passage >= 0.5) & (per_passage < 1.5)):.1%}")


if __name__ == "__main__":
    report(Path(sys.argv[1]))
