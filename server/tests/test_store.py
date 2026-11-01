from pathlib import Path

from core.pack import Column, GrammarItem, Occurrence, Passage, Source, Word
from store.pack import (
    read_pack,
    write_pack,
)
from store.texts import Page, open_texts, read_page, read_senses, read_translation, write_texts


def test_read_pack_merges_sound_spellings_and_keeps_kanji_spellings(tmp_path: Path) -> None:
    path = tmp_path / "pack.sqlite"
    source = Source("tatoeba", "Tatoeba", "CC BY 2.0 FR", "full")
    word = Word("w:1", ("分かる",), ("わかる",), ("to understand",), common=True)
    passages = [
        Passage("a", "tatoeba", 1, "わかった。ワカッタ。分かった。"),
        Passage("b", "tatoeba", 2, "。"),
    ]
    occurrences = [
        Occurrence("a", "w:1", "わかる", True, 0, 3, 1),
        Occurrence("a", "w:1", "ワカル", True, 4, 7, 1),
        Occurrence("a", "w:1", "分かる", False, 8, 11, 1),
    ]
    write_pack(path, {}, [source], [word], [], passages, occurrences)

    pack = read_pack(path)
    pairs = zip(pack.appearance_passages.tolist(), pack.appearance_columns.tolist(), strict=True)
    present: set[tuple[str, Column]] = {(pack.passages[p], pack.columns[c]) for p, c in pairs}

    assert pack.passages == ("a", "b")
    assert present == {("a", Column("w:1", None)), ("a", Column("w:1", "分かる"))}


def test_the_grammar_graph_survives_and_each_passage_keeps_its_highest_probability(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pack.sqlite"
    source = Source("tatoeba", "Tatoeba", "CC BY 2.0 FR", "full")
    uses = [
        GrammarItem("wa.topic", "use", ("sentence-shape",), nuance=False),
        GrammarItem("ne", "use", (), nuance=True),
    ]
    occurrences = [
        Occurrence("a", "wa.topic", "は", True, 1, 2, 0.5),
        Occurrence("a", "wa.topic", "は", True, 4, 5, 1.0),
    ]
    write_pack(path, {}, [source], [], uses, [Passage("a", "tatoeba", 1, "猫は犬は")], occurrences)

    pack = read_pack(path)
    assert pack.grammar == {item.id: item for item in uses}
    assert pack.appearance_probabilities.tolist() == [1.0]


def test_texts_for_the_learner_come_back_as_written(tmp_path: Path) -> None:
    path = tmp_path / "pack.sqlite"
    source = Source("tatoeba", "Tatoeba", "CC BY 2.0 FR", "full")
    word = Word("w:1", ("飲む",), ("のむ",), ("to drink",), common=True)
    page = Page("teiru", "form", "ている", "ている", "V-ている", "te", "key", "body")
    write_pack(path, {}, [source], [word], [], [Passage("a", "tatoeba", 1, "飲む。")], [])
    write_texts(
        path, {"a": "I drink."}, {"w:1": [["to drink", "to swallow"], ["to smoke"]]}, [page]
    )

    db = open_texts(path)
    assert read_translation(db, "a") == "I drink."
    assert read_translation(db, "b") is None
    assert read_senses(db, "w:1") == (("to drink", "to swallow"), ("to smoke",))
    assert read_page(db, "teiru") == page
    assert read_page(db, "teiru.ongoing") is None
