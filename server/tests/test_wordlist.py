from core.pack import Word
from integrations.wordlist import match

WAKARU = Word("w:1", ("分かる",), ("わかる",), ("to understand",))
KAKERU_HANG = Word("w:2", ("掛ける", "懸ける"), ("かける",), ("to hang",))
KAKERU_LACK = Word("w:3", ("欠ける",), ("かける",), ("to be lacking",))
COFFEE = Word("w:4", (), ("コーヒー",), ("coffee",))
WORDS = [WAKARU, KAKERU_HANG, KAKERU_LACK, COFFEE]
FREQUENCY = {"w:1": 30, "w:2": 10, "w:3": 50, "w:4": 5}


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
