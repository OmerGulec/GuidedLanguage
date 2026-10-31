import numpy as np

from core.pack import Column
from core.unknowns import unknowns
from tests.packs import pack_of

KANA_WAKARU = Column("w:1", None)
KANJI_WAKARU = Column("w:1", "分かる")
KOTO = Column("w:2", None)
IRU = Column("w:3", None)


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
