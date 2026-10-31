from pathlib import Path

from core.pack import Column, Occurrence, Passage, Source, Word
from store.pack import read_pack, write_pack


def test_read_pack_merges_sound_spellings_and_keeps_kanji_spellings(tmp_path: Path) -> None:
    path = tmp_path / "pack.sqlite"
    source = Source("tatoeba", "Tatoeba", "CC BY 2.0 FR", "full")
    word = Word("w:1", ("分かる",), ("わかる",), ("to understand",), common=True)
    passages = [
        Passage("a", "tatoeba", 1, "わかった。ワカッタ。分かった。"),
        Passage("b", "tatoeba", 2, "。"),
    ]
    occurrences = [
        Occurrence("a", "w:1", "わかる", True, 0, 3),
        Occurrence("a", "w:1", "ワカル", True, 4, 7),
        Occurrence("a", "w:1", "分かる", False, 8, 11),
    ]
    write_pack(path, {}, [source], [word], passages, occurrences)

    pack = read_pack(path)
    pairs = zip(pack.appearance_passages.tolist(), pack.appearance_columns.tolist(), strict=True)
    present: set[tuple[str, Column]] = {(pack.passages[p], pack.columns[c]) for p, c in pairs}

    assert pack.passages == ("a", "b")
    assert present == {("a", Column("w:1", None)), ("a", Column("w:1", "分かる"))}
