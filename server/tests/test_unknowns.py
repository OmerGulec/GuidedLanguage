import numpy as np

from core.candidates import frequency, ranked
from core.pack import Column, Pack
from core.unknowns import unknowns

KANA_WAKARU = Column("w:1", None)
KANJI_WAKARU = Column("w:1", "分かる")
KOTO = Column("w:2", None)
IRU = Column("w:3", None)


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


def test_unknowns_add_what_is_missing_from_each_value() -> None:
    pack = pack_of((KANJI_WAKARU, KOTO), (IRU,), ())
    values = np.array([0.25, 1.0, 0.5])
    assert unknowns(values, pack).tolist() == [0.75, 0.5, 0.0]


def test_raising_a_value_never_raises_a_passages_unknowns() -> None:
    rng = np.random.default_rng(0)
    pack = pack_of((KANA_WAKARU, KOTO), (KANJI_WAKARU, IRU, KOTO), (IRU,))
    for _ in range(200):
        before = rng.random(len(pack.columns))
        after = np.maximum(before, rng.random(len(pack.columns)))
        assert np.all(unknowns(after, pack) <= unknowns(before, pack))


def test_frequency_counts_a_passage_once_whatever_the_spelling() -> None:
    pack = pack_of((KANA_WAKARU, KANJI_WAKARU), (KANJI_WAKARU, KOTO), (IRU,))
    assert frequency(pack) == {"w:1": 2, "w:2": 1, "w:3": 1}


def test_ranking_orders_by_frequency_then_id_and_skips_excluded() -> None:
    counts = {"w:9": 5, "w:2": 3, "w:1": 3, "w:5": 7}
    assert ranked(counts, excluded={"w:5"}) == ["w:9", "w:1", "w:2"]
