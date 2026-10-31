import random
from datetime import datetime, timedelta

from core.events import Event, Introduced, LookedUp, Retracted, Reviewed
from core.memory import recall
from core.settings import Settings
from core.state import State, derive
from core.values import value
from tests.history import TOKYO, at, event

CARD = "w:1606560@分かる/recognize"
ITEM = "w:1606560"


def passed(when: datetime) -> Event:
    return event(when, Reviewed(CARD, passed=True, method="self"))


def failed(when: datetime) -> Event:
    return event(when, Reviewed(CARD, passed=False, method="self"))


def due(events: list[Event], settings: Settings = TOKYO) -> datetime:
    return derive(events, settings).cards[CARD].memory.due


def test_replay_ignores_arrival_order_and_duplicates() -> None:
    events = [
        event(at(1, 9), Introduced(ITEM, "new")),
        passed(at(1, 9)),
        failed(at(1, 10)),
        passed(at(2, 9)),
        passed(at(5, 20)),
    ]
    expected = derive(events, TOKYO)
    rng = random.Random(0)
    for _ in range(50):
        arrived = events + rng.sample(events, 2)
        rng.shuffle(arrived)
        assert derive(arrived, TOKYO) == expected


def test_retracting_a_review_undoes_it() -> None:
    first, second = passed(at(1, 9)), failed(at(2, 9))
    undone = derive([first, second, event(at(2, 10), Retracted(second.id))], TOKYO)
    assert undone == derive([first], TOKYO)


def test_multiple_choice_never_changes_memory() -> None:
    first = passed(at(1, 9))
    guess = event(at(2, 9), Reviewed(CARD, passed=False, method="choice"))
    assert derive([first, guess], TOKYO) == derive([first], TOKYO)


def test_graduating_needs_a_pass_on_a_later_study_day() -> None:
    history = [passed(at(1, 9)), passed(at(1, 23))]
    assert not derive(history, TOKYO).cards[CARD].graduated

    history.append(passed(at(2, 3)))  # before the 04:00 start, still the first study day
    assert not derive(history, TOKYO).cards[CARD].graduated

    history.append(passed(at(2, 5)))
    assert derive(history, TOKYO).cards[CARD].graduated


def test_only_on_time_failures_of_graduated_cards_are_lapses() -> None:
    history = [passed(at(1, 9)), failed(at(1, 10)), passed(at(1, 11))]
    assert derive(history, TOKYO).cards[CARD].lapses == 0

    history.append(passed(at(2, 9)))
    history.append(failed(due(history)))
    assert derive(history, TOKYO).cards[CARD].lapses == 1

    history.append(passed(due(history)))
    history.append(failed(due(history) + timedelta(days=30)))
    assert derive(history, TOKYO).cards[CARD].lapses == 1


def test_repeated_lapses_suspend_until_the_item_is_retaught() -> None:
    settings = Settings(zone=TOKYO.zone, lapses_before_suspension=2)
    history = [passed(at(1, 9)), passed(at(2, 9))]
    for _ in range(2):
        history.append(failed(due(history, settings)))
        history.append(passed(due(history, settings)))
    assert derive(history, settings).cards[CARD].suspended

    reteach = event(due(history, settings), Introduced(ITEM, "reteach"))
    state: State = derive([*history, reteach], settings)
    assert not state.cards[CARD].suspended
    assert state.cards[CARD].lapses == 0
    assert ITEM in state.made_due


def test_value_is_zero_until_passed_one_while_on_schedule_then_recall_chance() -> None:
    assert value(None, at(1, 9), TOKYO) == 0.0

    card = derive([passed(at(1, 9))], TOKYO).cards[CARD]
    next_day = at(2, 9)
    assert (
        TOKYO.retention <= recall(card.memory, next_day, TOKYO) < value(card, next_day, TOKYO) == 1
    )

    much_later = at(60, 9)
    assert 0.0 < value(card, much_later, TOKYO) == recall(card.memory, much_later, TOKYO) < 0.9

    lapsed = derive([passed(at(1, 9)), failed(at(1, 10))], TOKYO).cards[CARD]
    assert value(lapsed, at(1, 11), TOKYO) == 0.0


def test_lookup_makes_the_item_due_next_study_day_until_reviewed() -> None:
    lookup = event(at(3, 2), LookedUp(ITEM, "p1", "分かる", "よく分かる。"))
    assert derive([passed(at(1, 9)), lookup], TOKYO).made_due[ITEM] == at(3, 9).date()

    reviewed = derive([passed(at(1, 9)), lookup, passed(at(3, 9))], TOKYO)
    assert ITEM not in reviewed.made_due
