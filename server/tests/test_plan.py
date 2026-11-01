from dataclasses import replace
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from core.candidates import candidates, ranking
from core.cards import Card
from core.events import Event, Introduced, LookedUp, Marked, Modality, Reviewed
from core.pack import Column, GrammarItem
from core.plan import Plan, Situation, plan
from core.settings import Settings
from core.state import derive
from tests.history import TOKYO, at, event
from tests.packs import everywhere, pack_of

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
RANKING = ranking(PACK, TOKYO, everywhere(PACK))
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
            today,
            both,
            pack,
            ranking(pack, settings, everywhere(pack)),
            "reader",
            Situation(),
            settings,
            at(1, 9),
        ).passages["reading"]

    assert picks(frozenset()) == ("p2", "p1", "p0")
    assert picks(frozenset({"p2"})) == ("p1", "p0", "p3")


# Grammar: a system, a formation built on it, a frequent use built on the formation, a use
# that needs nothing, and a word.
SHAPE = GrammarItem("verb-classes", "system", (), nuance=False)
TE = GrammarItem("te-ta", "formation", ("verb-classes",), nuance=False)
TEIRU = GrammarItem("teiru.ongoing", "use", ("te-ta",), nuance=False)
TOPIC = GrammarItem("wa.topic", "use", (), nuance=False)
GRAMMAR_PACK = pack_of(
    *[(Column(TEIRU.id, None), Column(TOPIC.id, None), IN_KANJI)] * 9,
    (KOTO_IN_KANA,),
    graph=[SHAPE, TE, TEIRU, TOPIC],
)
GRAMMAR_RANKING = ranking(GRAMMAR_PACK, TOKYO, everywhere(GRAMMAR_PACK))
TEIRU_SENTENCE = Card((TEIRU.id,), None, "sentence").id
TOPIC_SENTENCE = Card((TOPIC.id,), None, "sentence").id
TE_UNDO = Card((TE.id,), None, "undo").id


def grammar_plan(history: list[Event], day: int, settings: Settings = TOKYO) -> Plan:
    nothing: NDArray[np.float64] = np.zeros(len(GRAMMAR_PACK.passages))
    unknowns: dict[Modality, NDArray[np.float64]] = {"reading": nothing, "listening": nothing}
    state = derive(history, settings)
    return plan(
        state, unknowns, GRAMMAR_PACK, GRAMMAR_RANKING, "reader", Situation(), settings, at(day, 20)
    )


def test_rank_is_frequency_over_effort_and_building_blocks_take_their_best_dependent() -> None:
    rank = GRAMMAR_RANKING.rank
    assert rank[WAKARU] == 9 and rank[TOPIC.id] == rank[TEIRU.id] == 9 / TOKYO.grammar_effort
    assert rank[TE.id] == rank[SHAPE.id] == rank[TEIRU.id]
    halved = pack_of(
        (Column(TOPIC.id, None),) * 1,
        probabilities={Column(TOPIC.id, None): 0.5},
        grammar={TOPIC.id},
    )
    assert ranking(halved, TOKYO, everywhere(halved)).frequency == {TOPIC.id: 0.5}


def test_grammar_waits_for_what_it_builds_on_and_a_system_is_offered_by_its_id() -> None:
    def offered(history: list[Event]) -> list[str]:
        return candidates(derive(history, TOKYO), GRAMMAR_RANKING, "reader")

    assert offered([]) == [RECOGNIZE, SHAPE.id, TOPIC_SENTENCE, KOTO_RECOGNIZE]
    shown = [event(at(1, 8), Introduced(SHAPE.id, "new"))]
    assert TE_UNDO in offered(shown) and TEIRU_SENTENCE not in offered(shown)
    formed = [*shown, *learned(TE_UNDO, TE.id)]
    assert TEIRU_SENTENCE in offered(formed)


def test_new_grammar_spends_the_new_budget_and_stops_at_the_grammar_cap() -> None:
    settings = replace(TOKYO, grammar_cap=1, new_budget=3)
    assert grammar_plan([], 1, settings).new == (RECOGNIZE, SHAPE.id, KOTO_RECOGNIZE)
    shown = [event(at(1, 9), Introduced(SHAPE.id, "new"))]
    assert grammar_plan(shown, 1, settings).new == (RECOGNIZE, KOTO_RECOGNIZE)


def test_a_marked_item_comes_up_for_review_sooner_when_nobody_checked_it() -> None:
    def first_due(reason: Literal["hand", "import"]) -> int:
        history = [event(at(1, 8), Marked(TOPIC.id, "known", reason))]
        return next(d for d in range(1, 200) if TOPIC_SENTENCE in grammar_plan(history, d).reviews)

    assert first_due("hand") <= TOKYO.doubtful_review_days + 1
    assert first_due("import") > TOKYO.marked_stability_days


def test_a_failed_first_review_withdraws_the_mark_reteaches_and_brings_its_dependents_due() -> None:
    marks = [event(at(1, 8), Marked(i, "known", "hand")) for i in (SHAPE.id, TE.id, TEIRU.id)]
    history = [*marks, review(TE_UNDO, 2, passed=False)]
    state = derive(history, TOKYO)
    assert TE.id not in state.marks and TEIRU.id in state.marks
    assert grammar_plan(history, 2).reteach == (TE.id,)
    assert TEIRU_SENTENCE not in grammar_plan(history, 2).reviews
    assert TEIRU_SENTENCE in grammar_plan(history, 3).reviews
