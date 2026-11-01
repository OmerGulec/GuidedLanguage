import sys
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np

from core.candidates import candidates, ranking
from core.cards import Card
from core.events import Event, Marked
from core.pack import Word
from core.settings import Settings
from core.state import derive
from core.unknowns import unknowns
from core.values import values
from langs.ja.analyser import hiragana, is_kana
from langs.ja.content import rows
from store.pack import read_pack, read_words
from store.paths import PACK

SHOWN = 15
SURU = "する"


@dataclass(frozen=True, slots=True)
class Matches:
    known: dict[str, str]
    # Words that fit several entries: the entry most common in the library comes first.
    guessed: dict[str, tuple[str, ...]]
    missing: list[str]


def read_word_list(path: Path) -> list[tuple[str, str | None]]:
    """One word per line, its reading optionally after a tab or a slash (Renshuu exports)."""
    words: list[tuple[str, str | None]] = []
    for row in rows(path):
        if len(row) > 1:
            spelling, reading = row[0], row[1]
        else:
            spelling, _, reading = row[0].partition("/")
        words.append((spelling, reading or None))
    return words


def match(
    wanted: Iterable[tuple[str, str | None]], words: Iterable[Word], frequency: Mapping[str, float]
) -> Matches:
    by_form: dict[str, list[Word]] = defaultdict(list)
    for word in words:
        for form in {*word.spellings, *word.readings, *map(hiragana, word.readings)}:
            by_form[form].append(word)

    def candidates(spelling: str, reading: str | None) -> list[Word]:
        found = {w.id: w for f in (spelling, hiragana(spelling)) for w in by_form.get(f, [])}
        fitting = [
            w
            for w in found.values()
            if reading is None or hiragana(reading) in map(hiragana, w.readings)
        ]
        # Katakana input should not land on a hiragana-only word that sounds the same.
        exact = [w for w in fitting if spelling in (*w.spellings, *w.readings)]

        def main_form(word: Word) -> bool:
            # A word without kanji has no single main form: JMdict files じゃ under じゃあ.
            if not word.spellings:
                heads = word.readings
            elif is_kana(spelling):
                heads = word.readings[:1]
            else:
                heads = word.spellings[:1]
            return hiragana(spelling) in map(hiragana, heads)

        return sorted(
            exact or fitting,
            key=lambda w: (not main_form(w), not w.common, -frequency.get(w.id, 0), w.id),
        )

    known: dict[str, str] = {}
    guessed: dict[str, tuple[str, ...]] = {}
    missing: list[str] = []
    for spelling, reading in wanted:
        found = candidates(spelling, reading)
        if not found and spelling.endswith(SURU) and spelling != SURU:
            # Lists often add する to a noun; the dictionary files the word under the noun.
            stem_reading = reading.removesuffix(SURU) if reading else None
            found = candidates(spelling.removesuffix(SURU), stem_reading)

        line = spelling if reading is None else f"{spelling} ({reading})"
        if len(found) == 1:
            known[line] = found[0].id
        elif found:
            guessed[line] = tuple(w.id for w in found)
        else:
            missing.append(line)
    return Matches(known, guessed, missing)


def report(path: Path) -> None:
    pack, words = read_pack(PACK), read_words(PACK)
    settings = Settings()
    pack_ranking = ranking(pack, settings)
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
    state = derive(marks, settings)
    tomorrow = imported_at + timedelta(days=1)
    per_passage = unknowns(values(state, pack, settings, tomorrow, "reading"), pack)
    print(f"passages fully known: {np.mean(per_passage < 0.5):.1%}")
    print(f"passages with one unknown: {np.mean((per_passage >= 0.5) & (per_passage < 1.5)):.1%}")

    next_words = candidates(state, pack_ranking, "reader")[:SHOWN]
    print("most frequent words not yet known:")
    print("  " + ", ".join(labels[Card.parse(card).items[0]] for card in next_words))


if __name__ == "__main__":
    report(Path(sys.argv[1]))
