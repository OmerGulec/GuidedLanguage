from datetime import datetime

import numpy as np
from numpy.typing import NDArray

from core.cards import Card
from core.events import Modality
from core.memory import recall
from core.pack import Pack
from core.settings import Settings
from core.state import CardState, State, starting


def value(card: CardState | None, at: datetime, settings: Settings) -> float:
    if card is None or not card.passed:
        return 0.0
    chance = recall(card.memory, at, settings)
    return 1.0 if chance >= settings.retention else chance


def values(
    state: State, pack: Pack, settings: Settings, at: datetime, modality: Modality
) -> NDArray[np.float64]:
    """Each column's value: the best card that lets the learner understand it (013)."""
    by_spelling: dict[tuple[str, str], float] = {}
    by_sound: dict[str, float] = {}
    by_ear: dict[str, float] = {}
    by_sentence: dict[str, float] = {}
    for card_id, card_state in state.cards.items():
        card, card_value = Card.parse(card_id), value(card_state, at, settings)
        item = card.items[0]
        if card.rung == "recognize" and card.spelling is not None:
            by_spelling[item, card.spelling] = card_value
        if card.rung in ("recognize", "listen"):
            by_sound[item] = max(by_sound.get(item, 0.0), card_value)
        if card.rung == "listen":
            by_ear[item] = card_value
        if card.rung == "sentence":
            by_sentence[item] = card_value

    known_without_reviews = {
        item: value(starting(item, mark, settings), at, settings)
        for item, mark in state.marks.items()
        if mark.status == "known" and item not in by_sound and item not in by_sentence
    }
    ignored = {item for item, mark in state.marks.items() if mark.status == "ignored"}

    def column_value(item: str, spelling: str | None) -> float:
        if item in ignored or item in pack.nuance:
            return 1.0
        # A grammar use is understood by ear as by eye through its sentence card (013).
        if item in pack.grammar:
            return by_sentence.get(item, known_without_reviews.get(item, 0.0))
        if modality == "listening":
            return by_ear.get(item, 0.0)
        marked = known_without_reviews.get(item, 0.0)
        if spelling is None:
            return by_sound.get(item, marked)
        return by_spelling.get((item, spelling), marked)

    return np.array([column_value(c.item, c.spelling) for c in pack.columns], dtype=np.float64)
