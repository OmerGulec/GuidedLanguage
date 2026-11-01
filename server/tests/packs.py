from collections.abc import Iterable, Mapping, Set

import numpy as np
from numpy.typing import NDArray

from core.pack import Column, GrammarItem, Pack


def everywhere(pack: Pack) -> NDArray[np.bool_]:
    """Every passage eligible to be shown."""
    return np.ones(len(pack.passages), dtype=np.bool_)


def pack_of(
    *passages: tuple[Column, ...],
    probabilities: Mapping[Column, float] | None = None,
    grammar: Set[str] = frozenset(),
    nuance: Set[str] = frozenset(),
    graph: Iterable[GrammarItem] = (),
) -> Pack:
    """A pack of the given passages. `grammar` names uses with no prerequisites; `graph` adds
    grammar items in full."""
    columns = list(dict.fromkeys(c for passage in passages for c in passage))
    appearances = [(p, columns.index(c)) for p, passage in enumerate(passages) for c in passage]
    chances = probabilities or {}
    items = {use: GrammarItem(use, "use", (), use in nuance) for use in grammar}
    items |= {item.id: item for item in graph}
    return Pack(
        passages=tuple(f"p{i}" for i in range(len(passages))),
        sources=("tatoeba",),
        passage_sources=np.zeros(len(passages), dtype=np.int32),
        columns=tuple(columns),
        appearance_passages=np.array([p for p, _ in appearances], dtype=np.int32),
        appearance_columns=np.array([c for _, c in appearances], dtype=np.int32),
        appearance_probabilities=np.array(
            [chances.get(columns[c], 1.0) for _, c in appearances], dtype=np.float64
        ),
        grammar=items,
    )
