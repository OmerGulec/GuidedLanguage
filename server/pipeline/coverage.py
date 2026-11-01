from datetime import UTC, datetime

import numpy as np

from core.candidates import ranked, ranking
from core.events import Event, Marked
from core.settings import Settings
from core.state import derive
from core.unknowns import unknowns
from core.values import values
from store.pack import read_eligible, read_pack
from store.paths import PACK

KNOWN_WORDS = (100, 250, 500, 1000, 2000, 3000, 5000, 10000)
MARKED_AT = datetime(2026, 1, 1, tzinfo=UTC)
MEASURED_AT = datetime(2026, 1, 2, tzinfo=UTC)


def report() -> None:
    pack = read_pack(PACK)
    settings = Settings()
    order = ranked(ranking(pack, settings, read_eligible(PACK)).frequency, excluded=frozenset())

    print("words known  fully known  one unknown")
    for count in KNOWN_WORDS:
        marks = [
            Event(f"mark-{item}", MARKED_AT, "report", Marked(item, "known", "hand"))
            for item in order[:count]
        ]
        state = derive(marks, settings)
        per_passage = unknowns(values(state, pack, settings, MEASURED_AT, "reading"), pack)
        print(
            f"{count:>11}  {np.mean(per_passage == 0):>11.1%}  {np.mean(per_passage == 1):>11.1%}"
        )


if __name__ == "__main__":
    report()
