from pathlib import Path

from langs.ja.analyser import Analyser, Lexicon
from langs.ja.content import rows


def check_links(analyser: Analyser, lexicon: Lexicon, path: Path) -> list[str]:
    """Words that must link to a given dictionary entry; returns a line for each that does not."""
    failures: list[str] = []
    for sentence, surface, spelling, reading in rows(path):
        entries = {token.surface: lexicon.entry(token) for token in analyser.words(sentence)}
        entry = entries.get(surface)
        if entry is None:
            failures.append(f"{sentence} {surface}: not linked, expected {spelling} ({reading})")
        elif spelling not in (*entry.spellings, *entry.readings) or reading not in entry.readings:
            found = f"{(entry.spellings or entry.readings)[0]} ({entry.readings[0]})"
            failures.append(
                f"{sentence} {surface}: linked to {found}, expected {spelling} ({reading})"
            )
    return failures
