import numpy as np

from core.pack import Column, Pack


def pack_of(*passages: tuple[Column, ...]) -> Pack:
    columns = list(dict.fromkeys(c for passage in passages for c in passage))
    appearances = [(p, columns.index(c)) for p, passage in enumerate(passages) for c in passage]
    return Pack(
        passages=tuple(f"p{i}" for i in range(len(passages))),
        sources=("tatoeba",),
        passage_sources=np.zeros(len(passages), dtype=np.int32),
        columns=tuple(columns),
        appearance_passages=np.array([p for p, _ in appearances], dtype=np.int32),
        appearance_columns=np.array([c for _, c in appearances], dtype=np.int32),
    )
