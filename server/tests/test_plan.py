from dataclasses import replace

import numpy as np
from numpy.typing import NDArray

from core.candidates import candidates, ranking
from core.cards import Card
from core.events import Event, Introduced, LookedUp, Marked, Modality, Reviewed
from core.pack import Column
from core.plan import Plan, Situation, plan
from core.settings import Settings
from core.state import derive
from tests.history import TOKYO, at, event
from tests.packs import pack_of

WAKARU, KOTO = "w:1606560", "w:1313580"
IN_KANA, IN_KANJI, KOTO_IN_KANA = Column(WAKARU, None), Column(WAKARU, "分かる"), Column(KOTO, None)
PACK = pack_of(
    (IN_KANJI,),
    (IN_KANJI,),
    (IN_KANJI,),
    (IN_KANA,),
    (KOTO_IN_KANA,),
    (KOTO_IN_KANA,),
    (KOTO_IN_KANA,),
)
RANKING = ranking(PACK)
RECOGNIZE = Card((WAKARU,), "分かる", "recognize").id
LISTEN = Card((WAKARU,), None, "listen").id
KOTO_RECOGNIZE = Card((KOTO,), None, "recognize").id


def review(card: str, day: int, passed: bool = True, hour: int = 9) -> Event:
    return event(at(day, hour), Reviewed(card, passed=passed, method="self"))


def learned(card: str, item: str = WAKARU) -> list[Event]:
    return [event(at(1, 8), Introduced(item, "new")), review(card, 1), review(card, 2)]


def planned(history: list[Event], day: int, settings: Settings = TOKYO, **situation: bool) -> Plan:
    state = derive(history, settings)
    nothing_unknown = np.zeros(len(PACK.passages))
    unknowns: dict[Modality, NDArray[np.float64]] = {
        "reading": nothing_unknown,
        "listening": nothing_unknown,
    }
    return plan(
        state, unknowns, PACK, RANKING, "listener", Situation(**situation), settings, at(day, 20)
    )


def test_grammar_is_not_ranked_among_words() -> None:
    topic = Column("wa.topic", None)
    assert ranking(pack_of((IN_KANJI, topic), (topic,), grammar={topic.item})).frequency == {
        WAKARU: 1
    }


def test_new_items_start_in_their_most_common_spelling_most_frequent_first() -> None:
    assert candidates(derive([], TOKYO), RANKING, "reader") == [RECOGNIZE, KOTO_RECOGNIZE]


def test_a_later_rung_unlocks_once_the_previous_graduates_and_only_if_the_goal_has_it() -> None:
    first_day = [event(at(1, 8), Introduced(WAKARU, "new")), review(RECOGNIZE, 1)]
    assert LISTEN not in candidates(derive(first_day, TOKYO), RANKING, "listener")

    graduated = derive([*first_day, review(RECOGNIZE, 2)], TOKYO)
    assert LISTEN in candidates(graduated, RANKING, "listener")
    assert LISTEN not in candidates(graduated, RANKING, "reader")


def test_marked_known_unlocks_the_next_rung_and_ignored_items_never_return() -> None:
    marks = [
        event(at(1, 8), Marked(WAKARU, "known", "hand")),
        event(at(1, 8), Marked(KOTO, "ignored", "hand")),
    ]
    assert candidates(derive(marks, TOKYO), RANKING, "listener") == [LISTEN]


def test_an_item_shown_but_never_answered_is_offered_again() -> None:
    shown = derive([event(at(1, 8), Introduced(WAKARU, "new"))], TOKYO)
    assert RECOGNIZE in candidates(shown, RANKING, "reader")


def test_cards_are_reviewed_when_due_and_not_before() -> None:
    history = learned(RECOGNIZE)
    due = derive(history, TOKYO).cards[RECOGNIZE].memory.due
    due_day = (due.astimezone(TOKYO.zone) - at(1, 4)).days + 1

    assert RECOGNIZE not in planned(history, due_day - 1).reviews
    assert RECOGNIZE in planned(history, due_day).reviews


def test_cards_outside_the_goal_are_kept_but_not_reviewed() -> None:
    cloze = Card((WAKARU,), None, "cloze").id
    history = [*learned(RECOGNIZE), review(cloze, 1), review(cloze, 2)]
    reviews = planned(history, 30).reviews
    assert RECOGNIZE in reviews
    assert cloze not in reviews


def test_without_sound_listening_cards_wait_and_only_reading_is_offered() -> None:
    history = [*learned(RECOGNIZE), review(LISTEN, 2, hour=10)]
    later = 30
    assert LISTEN in planned(history, later).reviews

    silent = planned(history, later, sound=False)
    assert LISTEN not in silent.reviews and RECOGNIZE in silent.reviews
    assert list(silent.passages) == ["reading"]


def test_suspended_items_are_retaught_first_out_of_the_new_budget() -> None:
    settings = replace(TOKYO, lapses_before_suspension=1, new_budget=2)
    history = learned(RECOGNIZE)
    due = derive(history, settings).cards[RECOGNIZE].memory.due
    history.append(event(due, Reviewed(RECOGNIZE, passed=False, method="self")))

    today = planned(history, 40, settings)
    assert today.reteach == (WAKARU,)
    assert len(today.new) == 1


def test_unlocked_rungs_get_their_own_allowance_beside_the_new_items() -> None:
    settings = replace(TOKYO, new_budget=1)
    history = learned(RECOGNIZE)
    assert planned(history, 3, settings).new == (LISTEN, KOTO_RECOGNIZE)

    history.append(review(LISTEN, 3, hour=10))
    assert planned(history, 3, settings).new == (KOTO_RECOGNIZE,)


def test_past_the_review_cap_the_most_frequent_items_come_first() -> None:
    history = [*learned(RECOGNIZE), *learned(KOTO_RECOGNIZE, KOTO)]
    assert planned(history, 60, replace(TOKYO, review_cap=1)).reviews == (RECOGNIZE,)


def test_the_cap_counts_todays_reviews_but_never_holds_back_learning_steps() -> None:
    history = [*learned(RECOGNIZE), *learned(KOTO_RECOGNIZE, KOTO)]
    capped = replace(TOKYO, review_cap=1)
    history.append(review(RECOGNIZE, 60, hour=8))
    assert planned(history, 60, capped).reviews == ()

    learning = [event(at(5, 8), Introduced(KOTO, "new")), review(KOTO_RECOGNIZE, 5, hour=8)]
    assert planned(learning, 5, replace(TOKYO, review_cap=0)).reviews == (KOTO_RECOGNIZE,)


def test_after_a_review_the_items_other_cards_wait_the_spacing() -> None:
    history = [*learned(RECOGNIZE), review(LISTEN, 2, hour=10), review(RECOGNIZE, 30)]
    assert LISTEN not in planned(history, 30).reviews
    assert LISTEN not in planned(history, 30 + TOKYO.spacing_days - 1).reviews
    assert LISTEN in planned(history, 30 + TOKYO.spacing_days).reviews


def test_a_lookup_makes_the_first_rung_due_the_next_day() -> None:
    history = [*learned(RECOGNIZE), event(at(3, 12), LookedUp(WAKARU, "p0", "分かる", "分かる。"))]
    assert RECOGNIZE not in planned(history, 3).reviews
    assert RECOGNIZE in planned(history, 4).reviews


def test_reading_takes_the_fewest_unknowns_then_the_easiest_and_skips_read_passages() -> None:
    pack = pack_of(
        (IN_KANA,), (IN_KANA, KOTO_IN_KANA), (KOTO_IN_KANA,), (IN_KANJI, KOTO_IN_KANA), ()
    )
    unknowns = np.array([1.0, 0.0, 0.0, 2.0, 0.0])
    state = derive([], TOKYO)
    settings = replace(TOKYO, reading_per_day=3)

    def picks(read: frozenset[str]) -> tuple[str, ...]:
        today = replace(state, read={"reading": read, "listening": frozenset()})
        both: dict[Modality, NDArray[np.float64]] = {"reading": unknowns, "listening": unknowns}
        return plan(
            today, both, pack, ranking(pack), "reader", Situation(), settings, at(1, 9)
        ).passages["reading"]

    assert picks(frozenset()) == ("p2", "p1", "p0")
    assert picks(frozenset({"p2"})) == ("p1", "p0", "p3")
