from collections.abc import Mapping

import numpy as np
from numpy.typing import NDArray

from core.candidates import candidates, ranking
from core.cards import Card
from core.events import Event, Introduced, Marked, Modality, Reviewed
from core.pack import Column, GrammarItem, Pack
from core.passages import card_passages
from core.plan import Situation, plan
from core.state import derive
from core.unknowns import unknowns
from tests.history import TOKYO, at, event
from tests.packs import everywhere, pack_of

WAKARU, KOTO, NEKO = "w:1606560", "w:1313580", "w:1467640"
IN_KANJI, IN_KANA = Column(WAKARU, "分かる"), Column(WAKARU, None)
KOTO_IN_KANA, NEKO_IN_KANA = Column(KOTO, None), Column(NEKO, None)
RECOGNIZE = Card((WAKARU,), "分かる", "recognize").id
TOPIC = GrammarItem("wa.topic", "use", (), nuance=False)
TOPIC_IN = Column(TOPIC.id, None)
TOPIC_SENTENCE = Card((TOPIC.id,), None, "sentence").id


def chosen(
    pack: Pack,
    card: str,
    history: list[Event] | None = None,
    known: Mapping[Column, float] | None = None,
    eligible: NDArray[np.bool_] | None = None,
) -> str | None:
    values = np.array([(known or {}).get(c, 0.0) for c in pack.columns], dtype=np.float64)
    state = derive(history or [], TOKYO)
    shown_from = everywhere(pack) if eligible is None else eligible
    return card_passages([card], state, values, unknowns(values, pack), pack, shown_from)[card]


def shown(card: str, passage: str, day: int) -> Event:
    return event(at(day, 9), Reviewed(card, passed=True, method="self", passage=passage))


def test_the_rest_known_comes_first_then_the_shortest() -> None:
    pack = pack_of(
        (IN_KANJI, KOTO_IN_KANA), (IN_KANJI, NEKO_IN_KANA, IN_KANA), (IN_KANJI, NEKO_IN_KANA)
    )
    known = {NEKO_IN_KANA: 1.0, IN_KANA: 1.0}

    assert chosen(pack, RECOGNIZE, known=known) == "p2"


def test_a_kanji_card_shows_its_spelling_and_a_kana_card_the_word_in_kana() -> None:
    pack = pack_of((IN_KANA,), (IN_KANJI,))

    assert chosen(pack, RECOGNIZE) == "p1"
    assert chosen(pack, Card((WAKARU,), None, "recognize").id) == "p0"


def test_reviews_go_through_every_passage_before_one_repeats() -> None:
    pack = pack_of((IN_KANJI,), (IN_KANJI,), (IN_KANJI,))
    history = [event(at(1, 8), Introduced(WAKARU, "new", passage="p1"))]
    picks: list[str] = []
    for day in range(2, 7):
        pick = chosen(pack, RECOGNIZE, history)
        assert pick is not None
        picks.append(pick)
        history.append(shown(RECOGNIZE, pick, day))

    assert picks == ["p0", "p2", "p1", "p0", "p2"]


def test_the_rest_known_outweighs_a_fresh_passage_and_a_fresh_one_fewer_unknowns() -> None:
    unknown_rest = pack_of((IN_KANJI,), (IN_KANJI, KOTO_IN_KANA))
    assert chosen(unknown_rest, RECOGNIZE, [shown(RECOGNIZE, "p0", 1)]) == "p0"

    nearly_known_rest = pack_of((IN_KANJI, KOTO_IN_KANA), (IN_KANJI, NEKO_IN_KANA, IN_KANA))
    nearly = {KOTO_IN_KANA: 0.8, NEKO_IN_KANA: 1.0, IN_KANA: 1.0}
    assert chosen(nearly_known_rest, RECOGNIZE, known=nearly) == "p1"
    assert chosen(nearly_known_rest, RECOGNIZE, [shown(RECOGNIZE, "p1", 1)], nearly) == "p0"


def test_only_eligible_passages_are_shown() -> None:
    pack = pack_of((IN_KANJI,), (IN_KANJI, KOTO_IN_KANA))

    assert chosen(pack, RECOGNIZE, eligible=np.array([False, True])) == "p1"
    assert chosen(pack, RECOGNIZE, eligible=np.array([False, False])) is None


def test_a_grammar_card_shows_only_passages_that_settle_its_use_never_a_mere_share() -> None:
    settled = pack_of((TOPIC_IN, KOTO_IN_KANA), graph=[TOPIC])
    high_share = pack_of((TOPIC_IN,), probabilities={TOPIC_IN: 0.97}, graph=[TOPIC])

    assert chosen(settled, TOPIC_SENTENCE) == "p0"
    assert chosen(high_share, TOPIC_SENTENCE) is None


def test_a_use_no_passage_settles_is_neither_offered_nor_brought_due() -> None:
    marked = [event(at(1, 8), Marked(TOPIC.id, "known", "hand"))]
    learned = [
        event(at(1, 8), Introduced(TOPIC.id, "new")),
        event(at(1, 9), Reviewed(TOPIC_SENTENCE, passed=True, method="self")),
    ]
    nothing: dict[Modality, NDArray[np.float64]] = {
        "reading": np.zeros(1),
        "listening": np.zeros(1),
    }
    later = at(int(TOKYO.doubtful_review_days) + 1, 20)

    def offered_and_due(probability: float, eligible: bool = True) -> tuple[bool, bool, bool]:
        pack = pack_of((TOPIC_IN,), probabilities={TOPIC_IN: probability}, graph=[TOPIC])
        pack_ranking = ranking(pack, TOKYO, np.array([eligible]))

        def due(history: list[Event]) -> bool:
            state = derive(history, TOKYO)
            today = plan(state, nothing, pack, pack_ranking, "reader", Situation(), TOKYO, later)
            return TOPIC_SENTENCE in today.reviews

        offered = TOPIC_SENTENCE in candidates(derive([], TOKYO), pack_ranking, "reader")
        return offered, due(marked), due(learned)

    assert offered_and_due(1.0) == (True, True, True)
    assert offered_and_due(0.97) == (False, False, False)
    assert offered_and_due(1.0, eligible=False) == (False, False, False)
