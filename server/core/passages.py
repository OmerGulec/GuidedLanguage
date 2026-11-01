"""The passage a card shows (013)."""

from collections.abc import Iterable

import numpy as np
from numpy.typing import NDArray

from core.cards import Card
from core.pack import Column, Pack
from core.state import State

# A grammar use is settled in a passage only when certain there: a rule that leaves one use, or
# a label two models agree on. A share, however high, is true of the form, not of the passage.
SETTLED = 1.0
# Fewer unknowns than this besides the card's own, and the rest of the passage counts as known.
KNOWN_REST = 0.5


def card_passages(
    cards: Iterable[str],
    state: State,
    values: NDArray[np.float64],
    unknowns: NDArray[np.float64],
    pack: Pack,
    eligible: NDArray[np.bool_],
) -> dict[str, str | None]:
    """The passage each card shows, from the eligible passages holding the card's column: the
    rest known if possible; then one the item has not shown, or else showed longest ago; then
    the fewest other unknowns; then the fewest items. None when no passage qualifies or the
    card holds no column. Values and unknowns are the plan's, for reading."""
    index = {column: i for i, column in enumerate(pack.columns)}
    columns = {card: _column(Card.parse(card), index) for card in cards}
    wanted = np.array(sorted({c for c in columns.values() if c is not None}), dtype=np.int32)

    # Every appearance of a wanted column in an eligible passage, grouped by column.
    rows = np.flatnonzero(
        np.isin(pack.appearance_columns, wanted) & eligible[pack.appearance_passages]
    )
    rows = rows[np.argsort(pack.appearance_columns[rows], kind="stable")]
    grouped = pack.appearance_columns[rows]
    starts = dict(zip(wanted.tolist(), np.searchsorted(grouped, wanted).tolist(), strict=True))
    ends = dict(
        zip(wanted.tolist(), np.searchsorted(grouped, wanted, "right").tolist(), strict=True)
    )

    sizes = np.bincount(pack.appearance_passages, minlength=len(pack.passages))
    position = {passage: i for i, passage in enumerate(pack.passages)}
    chosen: dict[str, str | None] = {}
    for card, column in columns.items():
        if column is None:
            chosen[card] = None
            continue
        found = rows[starts[column] : ends[column]]
        passages = pack.appearance_passages[found]
        probabilities = pack.appearance_probabilities[found]
        if pack.columns[column].item in pack.grammar:
            settled = probabilities >= SETTLED
            passages, probabilities = passages[settled], probabilities[settled]
        if len(passages) == 0:
            chosen[card] = None
            continue

        rest = unknowns[passages] - probabilities * (1.0 - values[column])
        shown = [position[p] for p in state.shown.get(pack.columns[column].item, ())]
        age = np.full(len(pack.passages), -1, dtype=np.int64)
        age[np.array(shown, dtype=np.int64)] = np.arange(len(shown))
        order = np.lexsort((passages, sizes[passages], rest, age[passages], rest >= KNOWN_REST))
        chosen[card] = pack.passages[passages[order[0]]]
    return chosen


def settled_uses(pack: Pack, eligible: NDArray[np.bool_]) -> frozenset[str]:
    """Grammar uses that some eligible passage settles: only these can show a sentence card."""
    settled = (pack.appearance_probabilities >= SETTLED) & eligible[pack.appearance_passages]
    columns: list[int] = np.unique(pack.appearance_columns[settled]).tolist()
    return frozenset(pack.columns[c].item for c in columns if pack.columns[c].item in pack.grammar)


def _column(card: Card, index: dict[Column, int]) -> int | None:
    """The column a card's passage must hold. Pair cards hold none yet, and formations none at
    all, since they have no occurrences."""
    if len(card.items) != 1:
        return None
    return index.get(Column(card.items[0], card.spelling))
