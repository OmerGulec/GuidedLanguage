from collections.abc import Mapping, Set

import numpy as np

from core.pack import Pack


def frequency(pack: Pack) -> dict[str, int]:
    items = sorted({column.item for column in pack.columns})
    index = {item: i for i, item in enumerate(items)}
    item_of_column = np.array([index[column.item] for column in pack.columns], dtype=np.int64)

    # One count per passage that contains the item, whichever spellings it appears in.
    pairs = pack.appearance_passages.astype(np.int64) * len(items)
    pairs += item_of_column[pack.appearance_columns]
    counts = np.bincount(np.unique(pairs) % len(items), minlength=len(items))

    return {item: int(count) for item, count in zip(items, counts, strict=True) if count}


def ranked(frequency: Mapping[str, int], excluded: Set[str]) -> list[str]:
    return sorted((i for i in frequency if i not in excluded), key=lambda i: (-frequency[i], i))
