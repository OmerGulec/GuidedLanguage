import random
from dataclasses import replace
from datetime import date

from core.candidates import Ranking, ranked
from core.pack import Pack
from core.plan import Situation
from core.settings import Settings
from sim.learner import Learner, Simulation

START = date(2026, 1, 1)
IMPORTED_WORDS = 1000
IMPORT_POOL = 2000
THREE_MONTHS = 90
HEAVY_NEW_BUDGET = 20


def day_zero(pack: Pack, ranking: Ranking, settings: Settings) -> Simulation:
    return Simulation(Learner("day-zero", seed=1), pack, ranking, settings, START)


def importer(pack: Pack, ranking: Ranking, settings: Settings) -> Simulation:
    """About a thousand words brought from another app, mostly but not only the frequent ones."""
    simulation = Simulation(Learner("importer", seed=2), pack, ranking, settings, START)
    pool = ranked(ranking.frequency, excluded=frozenset())[:IMPORT_POOL]
    simulation.import_known(random.Random(2).sample(pool, min(IMPORTED_WORDS, len(pool))))
    return simulation


def three_months(pack: Pack, ranking: Ranking, settings: Settings) -> Simulation:
    simulation = Simulation(Learner("three-months", seed=3), pack, ranking, settings, START)
    simulation.run(THREE_MONTHS)
    return simulation


def heavy_user(pack: Pack, ranking: Ranking, settings: Settings) -> Simulation:
    learner = Learner("heavy-user", seed=4, goal="listener", situation=Situation())
    heavy = replace(settings, new_budget=HEAVY_NEW_BUDGET)
    simulation = Simulation(learner, pack, ranking, heavy, START)
    simulation.run(THREE_MONTHS)
    return simulation
