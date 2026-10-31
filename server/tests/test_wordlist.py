from pathlib import Path

from core.pack import Word
from integrations.wordlist import match, read_word_list

WAKARU = Word("w:1", ("分かる",), ("わかる",), ("to understand",), common=True)
KAKERU_HANG = Word("w:2", ("掛ける", "懸ける"), ("かける",), ("to hang",), common=True)
KAKERU_LACK = Word("w:3", ("欠ける",), ("かける",), ("to be lacking",), common=True)
COFFEE = Word("w:4", (), ("コーヒー",), ("coffee",), common=True)
EASY = Word("w:5", ("易々",), ("いい",), ("easily",), common=False)
GOOD = Word("w:6", ("良い",), ("いい",), ("good",), common=True)
BODY = Word("w:7", ("体",), ("たい",), ("body",), common=True)
TIE = Word("w:8", (), ("タイ",), ("tie",), common=True)
STUDY = Word("w:9", ("勉強",), ("べんきょう",), ("study",), common=True)
SNAKE = Word("w:10", ("蛇",), ("へび", "じゃ"), ("snake",), common=True)
WELL = Word("w:11", (), ("じゃ",), ("well then",), common=False)
WORDS = [WAKARU, KAKERU_HANG, KAKERU_LACK, COFFEE, EASY, GOOD, BODY, TIE, STUDY, SNAKE, WELL]
FREQUENCY = {"w:1": 30, "w:2": 10, "w:3": 50, "w:4": 5, "w:7": 80, "w:8": 1, "w:10": 40}


def test_spellings_and_kana_find_their_word() -> None:
    found = match([("分かる", None), ("わかる", None), ("コーヒー", None)], WORDS, FREQUENCY)
    assert found.known == {"分かる": "w:1", "わかる": "w:1", "コーヒー": "w:4"}


def test_a_reading_settles_a_spelling_and_a_wrong_reading_matches_nothing() -> None:
    found = match([("欠ける", "かける"), ("分かる", "わかった")], WORDS, FREQUENCY)
    assert found.known == {"欠ける (かける)": "w:3"}
    assert found.missing == ["分かる (わかった)"]


def test_kana_shared_by_several_words_is_guessed_most_common_first() -> None:
    found = match([("かける", None), ("猫", None)], WORDS, FREQUENCY)
    assert found.guessed == {"かける": ("w:3", "w:2")}
    assert found.missing == ["猫"]


def test_readings_may_follow_a_tab_or_a_slash(tmp_path: Path) -> None:
    words = tmp_path / "words.txt"
    words.write_text("会う/あう\nアパート\n欠ける\tかける\n")
    assert read_word_list(words) == [("会う", "あう"), ("アパート", None), ("欠ける", "かける")]


def test_a_common_word_beats_a_rare_one_even_if_stray_links_made_the_rare_one_frequent() -> None:
    frequency = {**FREQUENCY, "w:5": 3}
    assert match([("いい", None)], WORDS, frequency).guessed == {"いい": ("w:6", "w:5")}


def test_katakana_finds_the_katakana_word_not_a_more_frequent_homophone() -> None:
    assert match([("タイ", None)], WORDS, FREQUENCY).known == {"タイ": "w:8"}


def test_a_suru_verb_falls_back_to_its_noun() -> None:
    found = match([("勉強する", "べんきょうする")], WORDS, FREQUENCY)
    assert found.known == {"勉強する (べんきょうする)": "w:9"}


def test_the_word_whose_main_form_was_written_beats_one_where_it_is_a_minor_reading() -> None:
    assert match([("じゃ", None)], WORDS, FREQUENCY).guessed == {"じゃ": ("w:11", "w:10")}
