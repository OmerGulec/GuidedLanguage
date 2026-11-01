import json
from datetime import UTC, date, datetime

from core.cards import LADDERS, Card, LadderKind
from core.events import Introduced, Reviewed
from core.pack import Word
from core.settings import Settings
from core.state import derive
from integrations.renshuu import (
    GRAMMAR_MAP,
    RenshuuGrammar,
    RenshuuWord,
    read_grammar_map,
    replay,
    replay_grammar,
)
from pipeline.lessons import GRAMMAR, read_lessons

AU = Word("w:1198180", ("会う", "逢う"), ("あう",), ("to meet",), common=True)
STUDY = Word("w:1403020", ("勉強",), ("べんきょう",), ("study",), common=True)
KNOWN = {w.id: w for w in (AU, STUDY)}


def renshuu_word(
    vectors: dict[str, list[tuple[str, str]]],
    entry: str | None = "1198180",
    spelling: str = "会う",
    reading: str = "あう",
) -> RenshuuWord:
    history = {
        name: {"name": name, "study_history": [{"date": d, "correct": c} for d, c in answers]}
        for name, answers in vectors.items()
    }
    term = {
        "edict_ent": entry,
        "kanji_full": spelling,
        "hiragana_full": reading,
        "user_data": {"introduced_date": "2025/01/01", "study_vectors": history},
    }
    return RenshuuWord.model_validate_json(json.dumps(term))


def reviews(*words: RenshuuWord) -> list[tuple[str, bool, datetime]]:
    return [
        (e.payload.card, e.payload.passed, e.at)
        for e in replay(words, KNOWN).events
        if isinstance(e.payload, Reviewed)
    ]


def test_a_day_with_any_wrong_answer_is_one_failed_review() -> None:
    word = renshuu_word(
        {"Kanji > Kana": [("2025/01/02", "yes")], "Kanji > Meaning": [("2025/01/02", "no")]}
    )
    recognize = Card((AU.id,), "会う", "recognize").id
    assert reviews(word) == [(recognize, False, datetime(2025, 1, 2, 12, tzinfo=UTC))]


def test_each_vector_feeds_its_card_and_writing_is_left_out() -> None:
    day = [("2025/01/02", "yes")]
    names = ("Kana > Meaning", "Listening", "Meaning > Kana", "Kana > Kanji", "Writing")
    cards = {card for card, _, _ in reviews(renshuu_word(dict.fromkeys(names, day)))}
    assert cards == {Card((AU.id,), None, rung).id for rung in ("recognize", "listen", "cloze")}


def test_importing_again_adds_nothing() -> None:
    word = renshuu_word({"Kanji > Kana": [("2025/01/02", "yes"), ("2025/01/05", "yes")]})
    first, second = replay([word], KNOWN).events, replay([word], KNOWN).events
    assert [e.id for e in first] == [e.id for e in second]
    assert derive(first + second, Settings()) == derive(first, Settings())


def test_the_spelling_renshuu_showed_is_kept_if_the_dictionary_has_it() -> None:
    day = {"Kanji > Kana": [("2025/01/02", "yes")]}
    shown, unlisted = renshuu_word(day, spelling="逢う"), renshuu_word(day, spelling="遇う")
    assert reviews(shown)[0][0] == Card((AU.id,), "逢う", "recognize").id
    assert reviews(unlisted)[0][0] == Card((AU.id,), "会う", "recognize").id


def test_suru_verbs_without_an_entry_go_to_their_noun_and_unknown_entries_are_reported() -> None:
    day = {"Kanji > Kana": [("2025/01/02", "yes")]}
    suru = renshuu_word(day, entry=None, spelling="勉強する", reading="べんきょうする")
    missing = renshuu_word(day, entry="9999999", spelling="猫", reading="ねこ")
    imported = replay([suru, missing], KNOWN)
    introduced = [e.payload.item for e in imported.events if isinstance(e.payload, Introduced)]
    assert introduced == [STUDY.id]
    assert imported.unmatched == ["猫"]


def test_the_replayed_history_ends_on_the_last_answer() -> None:
    answers = [("2025/01/02", "yes"), ("2025/01/03", "yes"), ("2025/03/01", "yes")]
    state = derive(replay([renshuu_word({"Kanji > Kana": answers})], KNOWN).events, Settings())
    card = state.cards[Card((AU.id,), "会う", "recognize").id]
    assert card.graduated
    assert card.memory.last_review == datetime(2025, 3, 1, 12, tzinfo=UTC)


def renshuu_point(term: int, answers: list[tuple[str, str]], introduced: str) -> RenshuuGrammar:
    history = [{"date": d, "correct": c} for d, c in answers]
    vectors = {"Main": {"name": "Main", "study_history": history}}
    progress = {"introduced_date": introduced, "study_vectors": vectors}
    point = {"id": term, "title_japanese": f"point {term}", "user_data": progress}
    return RenshuuGrammar.model_validate_json(json.dumps(point))


def test_grammar_points_that_share_a_card_make_one_review_a_day_and_systems_are_introduced() -> (
    None
):
    exercised = {1: ("ka.question/sentence",), 2: ("ka.question/sentence", "adjective-classes")}
    points = [
        renshuu_point(1, [("2025/01/02", "yes")], "2025/01/01"),
        renshuu_point(2, [("2025/01/02", "no"), ("2025/01/03", "yes")], "2024/12/30"),
        renshuu_point(3, [("2025/01/02", "yes")], "2025/01/01"),
    ]
    imported = replay_grammar(points, exercised)
    reviews = [
        (e.payload.card, e.payload.passed)
        for e in imported.events
        if isinstance(e.payload, Reviewed)
    ]
    introduced = {
        e.payload.item: e.at.date() for e in imported.events if isinstance(e.payload, Introduced)
    }
    assert reviews == [("ka.question/sentence", False), ("ka.question/sentence", True)]
    assert introduced == {
        "ka.question": date(2024, 12, 30),
        "adjective-classes": date(2024, 12, 30),
    }
    assert imported.unmatched == ["point 3"]


def test_the_grammar_map_names_items_and_rungs_of_their_ladders() -> None:
    lessons = read_lessons(GRAMMAR)
    ladders: dict[str, LadderKind] = {"use": "grammar", "formation": "formation"}
    for targets in read_grammar_map(GRAMMAR_MAP).values():
        for target in targets:
            card = Card.parse(target) if "/" in target else None
            lesson = lessons[card.items[0] if card else target]
            if card is None:
                assert lesson.header.kind == "system", target
            else:
                rungs = [rung.name for rung in LADDERS[ladders[lesson.header.kind]]]
                assert card.rung in rungs, target
