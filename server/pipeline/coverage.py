import numpy as np

from core.candidates import frequency, ranked
from core.unknowns import unknowns
from pipeline.build import PACK
from store.pack import read_pack

KNOWN_WORDS = (100, 250, 500, 1000, 2000, 3000, 5000, 10000)


def report() -> None:
    pack = read_pack(PACK)
    order = ranked(frequency(pack), excluded=frozenset())

    print("words known  fully known  one unknown")
    for count in KNOWN_WORDS:
        known = set(order[:count])
        values = np.array([float(column.item in known) for column in pack.columns])
        per_passage = unknowns(values, pack)
        print(
            f"{count:>11}  {np.mean(per_passage == 0):>11.1%}  {np.mean(per_passage == 1):>11.1%}"
        )


if __name__ == "__main__":
    report()
