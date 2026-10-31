from collections.abc import Mapping, Set
from dataclasses import dataclass

import numpy as np

from core.cards import Card, Goal, Rung, ladder
from core.pack import Pack
from core.state import CardState, State


@dataclass(frozen=True, slots=True, eq=False)
class Ranking:
    frequency: Mapping[str, int]
    # Each item's most common spelling in the library; None for a sound spelling.
    spellings: Mapping[str, str | None]


def ranking(pack: Pack) -> Ranking:
    items = sorted({column.item for column in pack.columns})
    index = {item: i for i, item in enumerate(items)}
    item_of_column = np.array([index[column.item] for column in pack.columns], dtype=np.int64)

    # One count per passage that contains the item, whichever spellings it appears in.
    pairs = pack.appearance_passages.astype(np.int64) * len(items)
    pairs += item_of_column[pack.appearance_columns]
    counts = np.bincount(np.unique(pairs) % len(items), minlength=len(items))

    per_column = np.bincount(pack.appearance_columns, minlength=len(pack.columns))
    spellings: dict[str, str | None] = {}
    best: dict[str, int] = {}
    for column, count in zip(pack.columns, per_column.tolist(), strict=True):
        if count > best.get(column.item, -1):
            best[column.item], spellings[column.item] = count, column.spelling

    frequency = {item: int(n) for item, n in zip(items, counts.tolist(), strict=True) if n}
    return Ranking(frequency, spellings)


def ranked(frequency: Mapping[str, int], excluded: Set[str]) -> list[str]:
    return sorted((i for i in frequency if i not in excluded), key=lambda i: (-frequency[i], i))


def candidates(state: State, ranking: Ranking, goal: Goal) -> list[str]:
    """New cards in rank order: first rungs of new items, then rungs that just unlocked (009)."""
    rungs = ladder("word", goal)
    held = _held(state)
    found: list[tuple[str, str]] = []

    for item in ranking.frequency:
        mark = state.marks.get(item)
        if mark is not None and mark.status == "ignored":
            continue
        held_rungs = held.get(item, {})
        if mark is None and rungs[0].name not in held_rungs:
            found.append((item, Card((item,), ranking.spellings[item], rungs[0].name).id))
            continue
        card = _next_rung(item, rungs, held_rungs, marked_known=mark is not None)
        if card is not None:
            found.append((item, card))

    found.sort(key=lambda pair: (-ranking.frequency[pair[0]], pair[1]))
    return [card for _, card in found]


def _held(state: State) -> dict[str, dict[str, CardState]]:
    held: dict[str, dict[str, CardState]] = {}
    for card_id, card_state in state.cards.items():
        card = Card.parse(card_id)
        for item in card.items:
            rungs = held.setdefault(item, {})
            current = rungs.get(card.rung)
            if current is None or (card_state.graduated and not current.graduated):
                rungs[card.rung] = card_state
    return held


def _next_rung(
    item: str, rungs: tuple[Rung, ...], held: Mapping[str, CardState], marked_known: bool
) -> str | None:
    if any(card.suspended for card in held.values()):
        return None
    first = held.get(rungs[0].name)
    graduated = marked_known if first is None else first.graduated
    for rung in rungs[1:]:
        if rung.name not in held:
            return Card((item,), None, rung.name).id if graduated else None
        graduated = held[rung.name].graduated
    return None
