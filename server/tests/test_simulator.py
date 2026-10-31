from collections import Counter
from pathlib import Path

import pytest

from core.candidates import Ranking, candidates, ranking
from core.cards import Card
from core.pack import Pack
from core.settings import Settings
from core.state import derive
from core.unknowns import unknowns
from core.values import values
from sim.learner import Learner, Simulation
from sim.learners import START, day_zero, heavy_user, importer, three_months
from store.pack import read_pack

SETTINGS = Settings()
PACK = read_pack(Path(__file__).parent / "fixtures" / "pack.sqlite")
RANKING = ranking(PACK)


@pytest.fixture(scope="module")
def regular() -> Simulation:
    return three_months(PACK, RANKING, SETTINGS)


@pytest.fixture(scope="module")
def heavy() -> Simulation:
    return heavy_user(PACK, RANKING, SETTINGS)


def short_run(pack: Pack, ranking: Ranking, seed: int) -> Simulation:
    simulation = Simulation(Learner("short", seed), pack, ranking, SETTINGS, START)
    simulation.run(20)
    return simulation


def test_replaying_a_simulated_history_gives_the_state_built_along_the_way(
    regular: Simulation,
) -> None:
    assert derive(regular.events, SETTINGS) == regular.state


def test_a_seed_always_produces_the_same_learner_and_another_seed_does_not() -> None:
    first, again, other = (short_run(PACK, RANKING, seed) for seed in (7, 7, 8))
    assert first.events == again.events
    assert first.events != other.events


def test_no_study_day_starts_more_new_cards_than_the_budget(regular: Simulation) -> None:
    started = Counter(card.learned for card in regular.state.cards.values())
    assert max(started.values()) == SETTINGS.new_budget
    assert len(started) == len(regular.days)


def test_a_listening_card_starts_only_after_its_word_graduated(heavy: Simulation) -> None:
    cards = heavy.state.cards
    recognized = {
        Card.parse(card).items[0]: held for card, held in cards.items() if "/recognize" in card
    }
    listened = [
        (Card.parse(card).items[0], held) for card, held in cards.items() if "/listen" in card
    ]

    assert listened
    for item, held in listened:
        assert recognized[item].graduated
        assert held.learned > recognized[item].learned


def test_imported_words_count_as_known_and_are_not_taught_again() -> None:
    fresh, imported = day_zero(PACK, RANKING, SETTINGS), importer(PACK, RANKING, SETTINGS)
    at = imported.events[-1].at

    def total_unknowns(simulation: Simulation) -> float:
        return float(unknowns(values(simulation.state, PACK, SETTINGS, at, "reading"), PACK).sum())

    assert total_unknowns(imported) < total_unknowns(fresh)
    offered = {Card.parse(card).items[0] for card in candidates(imported.state, RANKING, "reader")}
    assert not offered & set(imported.state.marks)
