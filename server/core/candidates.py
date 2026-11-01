from collections.abc import Mapping, Set
from dataclasses import dataclass
from functools import cache

import numpy as np

from core.cards import LADDERS, Card, Goal, LadderKind, Rung, ladder
from core.pack import GrammarItem, Pack
from core.settings import Settings
from core.state import CardState, State

LADDER_OF: dict[str, LadderKind] = {"use": "grammar", "formation": "formation"}


@dataclass(frozen=True, slots=True, eq=False)
class Ranking:
    # Passages holding the item: a word counts each passage once, a grammar use by its highest
    # probability there (009).
    frequency: Mapping[str, float]
    # Frequency over effort; formations and systems take the rank of their best dependent.
    rank: Mapping[str, float]
    # Each word's most common spelling in the library; None for a sound spelling.
    spellings: Mapping[str, str | None]
    grammar: Mapping[str, GrammarItem]


def ranking(pack: Pack, settings: Settings) -> Ranking:
    items = sorted({column.item for column in pack.columns})
    index = {item: i for i, item in enumerate(items)}
    item_of_column = np.array([index[c.item] for c in pack.columns], dtype=np.int64)
    in_grammar = np.array([item in pack.grammar for item in items], dtype=bool)

    # One count per passage that contains the item, whichever spellings it appears in.
    pairs = pack.appearance_passages.astype(np.int64) * len(items)
    pairs += item_of_column[pack.appearance_columns]
    counts = np.bincount(np.unique(pairs) % len(items), minlength=len(items)).astype(float)
    # A grammar use has one column, so each of its appearances is a passage at its highest.
    chances = np.bincount(
        item_of_column[pack.appearance_columns],
        weights=pack.appearance_probabilities,
        minlength=len(items),
    )
    totals = np.where(in_grammar, chances, counts)

    per_column = np.bincount(pack.appearance_columns, minlength=len(pack.columns))
    spellings: dict[str, str | None] = {}
    best: dict[str, int] = {}
    for column, count in zip(pack.columns, per_column.tolist(), strict=True):
        if column.item not in pack.grammar and count > best.get(column.item, -1):
            best[column.item], spellings[column.item] = count, column.spelling

    frequency = {item: n for item, n in zip(items, totals.tolist(), strict=True) if n}
    return Ranking(frequency, _ranks(frequency, pack.grammar, settings), spellings, pack.grammar)


def _ranks(
    frequency: Mapping[str, float], grammar: Mapping[str, GrammarItem], settings: Settings
) -> dict[str, float]:
    dependents: dict[str, list[str]] = {}
    for item in grammar.values():
        for prerequisite in item.prerequisites:
            dependents.setdefault(prerequisite, []).append(item.id)

    @cache
    def rank(item: str) -> float:
        kind = grammar[item].kind if item in grammar else "word"
        if kind in ("formation", "system"):
            return max((rank(d) for d in dependents.get(item, ())), default=0.0)
        effort = settings.word_effort if kind == "word" else settings.grammar_effort
        return frequency.get(item, 0.0) / effort

    return {item: rank(item) for item in {*frequency, *grammar}}


def ranked(frequency: Mapping[str, float], excluded: Set[str]) -> list[str]:
    return sorted((i for i in frequency if i not in excluded), key=lambda i: (-frequency[i], i))


def candidates(state: State, ranking: Ranking, goal: Goal) -> list[str]:
    """New cards in rank order: first rungs of new items whose prerequisites are known, then
    rungs that just unlocked (009). A system has no cards; it is offered by its item id."""
    held = _held(state)
    found: list[tuple[str, str]] = []

    for item in ranking.rank:
        mark = state.marks.get(item)
        if mark is not None and mark.status == "ignored":
            continue
        grammar = ranking.grammar.get(item)
        if grammar is not None and not all(
            known(p, state, ranking, held) for p in grammar.prerequisites
        ):
            continue
        if grammar is not None and grammar.kind == "system":
            if mark is None and item not in state.introduced:
                found.append((item, item))
            continue

        rungs = ladder("word" if grammar is None else LADDER_OF[grammar.kind], goal)
        held_rungs = held.get(item, {})
        if mark is None and rungs[0].name not in held_rungs:
            spelling = ranking.spellings.get(item) if grammar is None else None
            found.append((item, Card((item,), spelling, rungs[0].name).id))
            continue
        card = _next_rung(item, rungs, held_rungs, marked_known=mark is not None)
        if card is not None:
            found.append((item, card))

    found.sort(key=lambda pair: (-ranking.rank[pair[0]], pair[1]))
    return [card for _, card in found]


def offered_item(offer: str, ranking: Ranking) -> str:
    """The item a candidate offers: a system by its id, anything else through its card."""
    return offer if offer in ranking.grammar else Card.parse(offer).items[0]


def known(
    item: str, state: State, ranking: Ranking, held: Mapping[str, Mapping[str, CardState]]
) -> bool:
    """Its first rung graduated and last passed, or it was marked known; a system once shown."""
    mark = state.marks.get(item)
    grammar = ranking.grammar.get(item)
    if grammar is not None and grammar.kind == "system":
        return item in state.introduced or (mark is not None and mark.status == "known")
    first = LADDERS["word" if grammar is None else LADDER_OF[grammar.kind]][0].name
    card = held.get(item, {}).get(first)
    if card is None:
        return mark is not None and mark.status == "known"
    return card.graduated and card.passed


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
