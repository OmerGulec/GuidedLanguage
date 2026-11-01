from pathlib import Path

import pytest

from core.pack import passage_id
from langs.ja.analyser import Analyser, Lexicon, Link, Token, read_readings, word
from langs.ja.checks import check_links
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
    return {t.surface: lexicon.link(t, e) for t, e in lexicon.words(analyser.tokens(text))}


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
        token = Token(
            surface="私",
            lemma="私",
            base="私",
            reading=reading,
            written_reading=reading,
            surface_reading=reading,
            part_of_speech="代名詞",
            subtype="*",
            conjugation="*",
            inflection="*",
            start=0,
            end=1,
        )
        assert lexicon.link(token, lexicon.entry(token)).item == item("私", reading)


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


def test_names_numbers_and_particles_are_not_words(analyser: Analyser, lexicon: Lexicon) -> None:
    assert list(links(analyser, lexicon, "東京に行く。")) == ["行く"]
    assert links(analyser, lexicon, "三") == {}


def test_unknown_word_gets_an_unresolved_item(analyser: Analyser, lexicon: Lexicon) -> None:
    token = next(t for t in analyser.tokens("猫だ。") if t.surface == "猫")
    assert links(analyser, lexicon, "猫だ。")["猫"].item == lexicon.unresolved(token).id
    assert lexicon.unresolved(token).id == "u:猫/ねこ"


def test_spans_point_at_the_surface_despite_spaces(analyser: Analyser, lexicon: Lexicon) -> None:
    text = "今日 は　お茶 を飲む。"
    words = [token for token, _ in lexicon.words(analyser.tokens(text))]
    assert [text[t.start : t.end] for t in words] == [t.surface for t in words]
    assert "お茶" in [t.surface for t in words]


def test_a_run_of_tokens_listed_as_one_word_is_one_word(
    analyser: Analyser, lexicon: Lexicon
) -> None:
    assert links(analyser, lexicon, "お茶を飲む。")["お茶"] == Link(
        item("お茶", "おちゃ"), "お茶", phonetic=False
    )
    assert links(analyser, lexicon, "おちゃを飲む。")["おちゃ"] == Link(
        item("お茶", "おちゃ"), "おちゃ", phonetic=True
    )


def test_a_compound_verb_ends_in_the_dictionary_form(analyser: Analyser, lexicon: Lexicon) -> None:
    found = links(analyser, lexicon, "子供が泣き出した。")["泣き出し"]
    assert found == Link(item("泣き出す", "なきだす"), "泣き出す", phonetic=False)


def test_the_longest_listed_run_wins(analyser: Analyser, lexicon: Lexicon) -> None:
    found = links(analyser, lexicon, "自動車事故があった。")
    assert found["自動車事故"].item == item("自動車事故", "じどうしゃじこ")


def test_names_and_changed_sounds_still_join(analyser: Analyser, lexicon: Lexicon) -> None:
    assert links(analyser, lexicon, "日本語を話す。")["日本語"].item == item("日本語", "にほんご")
    found = links(analyser, lexicon, "日曜日に行く。")
    assert found["日曜日"].item == item("日曜日", "にちようび")


def test_words_apart_in_the_text_stay_apart(analyser: Analyser, lexicon: Lexicon) -> None:
    assert list(links(analyser, lexicon, "日本 語を話す。")) == ["語", "話す"]


def test_set_phrases_are_read_as_their_parts(analyser: Analyser, lexicon: Lexicon) -> None:
    found = links(analyser, lexicon, "その時、雨が降った。")
    assert found["その"].item == item("其の", "その")
    assert found["時"].item == item("時", "とき")


def test_a_counter_stays_with_its_number(analyser: Analyser, lexicon: Lexicon) -> None:
    assert links(analyser, lexicon, "６時に起きた。")["時"].item == item("時", "じ")
    assert links(analyser, lexicon, "一日中働いた。")["日"].item == item("日", "にち")


def test_passage_id_ignores_width_and_surrounding_space() -> None:
    assert passage_id("tatoeba", "ＡＢＣです。 ") == passage_id("tatoeba", "ABCです。")
    assert passage_id("tatoeba", "です。") != passage_id("aozora", "です。")


def test_link_checks_report_words_linked_elsewhere_or_not_at_all(
    analyser: Analyser, lexicon: Lexicon, tmp_path: Path
) -> None:
    checks = tmp_path / "link-checks.tsv"
    checks.write_text(
        "# sentence\tword\tspelling\treading\n"
        "ここにいる。\tいる\t居る\tいる\n"
        "ここにいる。\tいる\t要る\tいる\n"
        "ここにいる。\tねこ\t猫\tねこ\n"
    )
    assert check_links(analyser, lexicon, checks) == [
        "ここにいる。 いる: linked to 居る (いる), expected 要る (いる)",
        "ここにいる。 ねこ: not linked, expected 猫 (ねこ)",
    ]
