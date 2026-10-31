from pathlib import Path

import pytest

from core.pack import passage_id
from langs.ja.analyser import Analyser, Lexicon, Link, Token, read_readings, word
from langs.ja.dictionary import Entry, read_jmdict

ENTRIES = list(read_jmdict(Path(__file__).parent / "fixtures" / "jmdict.xml"))
READINGS = read_readings(Path(__file__).parents[2] / "content" / "ja" / "readings.tsv")


@pytest.fixture(scope="module")
def analyser() -> Analyser:
    return Analyser()


@pytest.fixture(scope="module")
def lexicon() -> Lexicon:
    return Lexicon(ENTRIES, READINGS)


def item(spelling: str, reading: str) -> str:
    entry: Entry = next(
        e for e in ENTRIES if spelling in (*e.spellings, *e.readings) and reading in e.readings
    )
    return word(entry).id


def links(analyser: Analyser, lexicon: Lexicon, text: str) -> dict[str, Link]:
    return {t.surface: lexicon.link(t) for t in analyser.words(text)}


def test_kana_conjugation_links_to_the_dictionary_entry(
    analyser: Analyser, lexicon: Lexicon
) -> None:
    found = links(analyser, lexicon, "もうわかった。")["わかっ"]
    assert found == Link(item("分かる", "わかる"), "わかる", phonetic=True)


def test_kanji_surface_keeps_its_kanji_spelling(analyser: Analyser, lexicon: Lexicon) -> None:
    found = links(analyser, lexicon, "もう分かった。")["分かっ"]
    assert found == Link(item("分かる", "わかる"), "分かる", phonetic=False)


def test_reading_separates_words_that_share_a_spelling(lexicon: Lexicon) -> None:
    for reading in ("わたし", "あたし"):
        token = Token("私", "私", "私", reading, "代名詞", 0, 1)
        assert lexicon.link(token).item == item("私", reading)


def test_lemma_beats_other_words_with_the_same_reading(
    analyser: Analyser, lexicon: Lexicon
) -> None:
    assert links(analyser, lexicon, "ここにいる。")["いる"].item == item("居る", "いる")
    assert links(analyser, lexicon, "することがある。")["こと"].item == item("事", "こと")


def test_reading_corrections_replace_the_analysers_formal_reading(
    analyser: Analyser, lexicon: Lexicon
) -> None:
    assert links(analyser, lexicon, "私は行く。")["私"].item == item("私", "わたし")


def test_katakana_loanword_is_a_phonetic_spelling(analyser: Analyser, lexicon: Lexicon) -> None:
    found = links(analyser, lexicon, "コーヒーを飲む。")
    assert found["コーヒー"] == Link(item("コーヒー", "コーヒー"), "コーヒー", phonetic=True)
    assert found["飲む"].item == item("飲む", "のむ")


def test_names_numbers_and_particles_are_not_words(analyser: Analyser) -> None:
    assert [t.surface for t in analyser.words("東京に行く。")] == ["行く"]
    assert list(analyser.words("三")) == []


def test_unknown_word_gets_an_unresolved_item(analyser: Analyser, lexicon: Lexicon) -> None:
    token = next(t for t in analyser.words("猫だ。") if t.surface == "猫")
    assert lexicon.link(token).item == lexicon.unresolved(token).id == "u:猫/ねこ"


def test_spans_point_at_the_surface_despite_spaces(analyser: Analyser) -> None:
    text = "今日 は　とても 暑い。"
    assert all(text[t.start : t.end] == t.surface for t in analyser.words(text))


def test_passage_id_ignores_width_and_surrounding_space() -> None:
    assert passage_id("tatoeba", "ＡＢＣです。 ") == passage_id("tatoeba", "ABCです。")
    assert passage_id("tatoeba", "です。") != passage_id("aozora", "です。")
