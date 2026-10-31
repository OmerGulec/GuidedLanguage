import numpy as np
from numpy.typing import NDArray

from core.pack import Pack


def unknowns(values: NDArray[np.float64], pack: Pack) -> NDArray[np.float64]:
    misses = 1.0 - values[pack.appearance_columns]
    return np.bincount(pack.appearance_passages, weights=misses, minlength=len(pack.passages))
