from datetime import timedelta
from typing import Literal

from core.cards import Card
from core.events import Event, Marked, Modality, Reviewed
from core.pack import Column, Pack
from core.state import Mark, derive, starting
from core.unknowns import unknowns
from core.values import values
from tests.history import TOKYO, at, event
from tests.packs import pack_of

WAKARU, KOTO, IRU = "w:1606560", "w:1313580", "w:1577980"
IN_KANA, IN_KANJI = Column(WAKARU, None), Column(WAKARU, "分かる")
RECOGNIZE_IN_KANA = Card((WAKARU,), None, "recognize")
RECOGNIZE_IN_KANJI = Card((WAKARU,), "分かる", "recognize")
LISTEN = Card((WAKARU,), None, "listen")


def passed(card: Card, day: int = 1) -> Event:
    return event(at(day, 9), Reviewed(card.id, passed=True, method="self"))


def marked(item: str, status: Literal["known", "ignored"]) -> Event:
    return event(at(1, 9), Marked(item, status, "hand"))


def unknown_counts(events: list[Event], pack: Pack, modality: Modality) -> list[float]:
    state = derive(events, TOKYO)
    return unknowns(values(state, pack, TOKYO, at(2, 9), modality), pack).tolist()


def test_a_kana_card_does_not_teach_the_kanji_spelling_but_the_reverse_holds() -> None:
    pack = pack_of((IN_KANA,), (IN_KANJI,))
    assert unknown_counts([passed(RECOGNIZE_IN_KANA)], pack, "reading") == [0.0, 1.0]
    assert unknown_counts([passed(RECOGNIZE_IN_KANJI)], pack, "reading") == [0.0, 0.0]


def test_listening_counts_only_listening_cards_which_also_link_sound_and_meaning() -> None:
    pack = pack_of((IN_KANA,), (IN_KANJI,))
    assert unknown_counts([passed(RECOGNIZE_IN_KANJI)], pack, "listening") == [1.0, 1.0]
    assert unknown_counts([passed(LISTEN)], pack, "listening") == [0.0, 0.0]
    assert unknown_counts([passed(LISTEN)], pack, "reading") == [0.0, 1.0]


def test_marked_known_covers_reading_and_ignored_covers_everything() -> None:
    pack = pack_of((IN_KANA, Column(KOTO, None), Column(IRU, None)))
    marks = [marked(WAKARU, "known"), marked(KOTO, "ignored")]
    assert unknown_counts(marks, pack, "reading") == [1.0]
    assert unknown_counts(marks, pack, "listening") == [2.0]


def test_card_ids_round_trip_even_when_an_item_id_contains_a_slash() -> None:
    for card in (
        RECOGNIZE_IN_KANJI,
        Card(("u:猫/ねこ",), None, "listen"),
        Card(("w:1", "w:2"), None, "contrast"),
    ):
        assert Card.parse(card.id) == card
    assert RECOGNIZE_IN_KANJI.id == "w:1606560@分かる/recognize"


def test_a_marked_items_first_rung_continues_from_its_starting_memory() -> None:
    history = [marked(WAKARU, "known"), passed(RECOGNIZE_IN_KANA, day=10), passed(LISTEN, day=10)]
    cards = derive(history, TOKYO).cards

    first = cards[RECOGNIZE_IN_KANA.id]
    assert first.graduated and first.memory.stability > TOKYO.marked_stability_days

    later = cards[LISTEN.id]
    assert not later.graduated and later.memory.stability < TOKYO.marked_stability_days


def test_starting_memories_fall_due_spread_over_the_set_period() -> None:
    mark = Mark("known", at(1, 9))
    shortest = timedelta(days=TOKYO.marked_stability_days)
    longest = shortest + timedelta(days=TOKYO.marked_spread_days)

    dues = [starting(f"w:{n}", mark, TOKYO).memory.due - mark.at for n in range(200)]

    assert all(shortest <= due < longest for due in dues)
    assert len(set(dues)) > 150
    assert dues == [starting(f"w:{n}", mark, TOKYO).memory.due - mark.at for n in range(200)]
