from dataclasses import replace

import numpy as np

from core.candidates import ranking
from core.plan import Situation
from core.settings import Settings
from core.unknowns import unknowns
from core.values import values
from sim.learner import Learner, Simulation
from sim.learners import HEAVY_NEW_BUDGET, START
from store.pack import read_pack
from store.paths import PACK

MONTHS = 6
DAYS_PER_MONTH = 30


def report() -> None:
    pack = read_pack(PACK)
    pack_ranking = ranking(pack)
    settings = Settings()
    learners = [
        (Learner("regular", seed=3), settings),
        (
            Learner("heavy", seed=4, goal="listener", situation=Situation()),
            replace(settings, new_budget=HEAVY_NEW_BUDGET),
        ),
    ]

    for learner, learner_settings in learners:
        print(f"\n{learner.name}: {learner.goal}, {learner_settings.new_budget} new words a day")
        print("month  reviews/day  busiest day  failed  cards  fully known  one unknown")
        simulation = Simulation(learner, pack, pack_ranking, learner_settings, START)
        for month in range(1, MONTHS + 1):
            simulation.run(DAYS_PER_MONTH)
            days = simulation.days[-DAYS_PER_MONTH:]
            reviews = [d.reviews for d in days]
            failed = sum(d.failed for d in days) / max(1, sum(reviews))
            at = simulation.events[-1].at
            per_passage = unknowns(
                values(simulation.state, pack, learner_settings, at, "reading"), pack
            )
            print(
                f"{month:>5}  {np.mean(reviews):>11.0f}  {max(reviews):>11}  {failed:>6.1%}"
                f"  {len(simulation.state.cards):>5}  {np.mean(per_passage < 0.5):>11.1%}"
                f"  {np.mean(per_passage < 1.5):>11.1%}"
            )


if __name__ == "__main__":
    report()
