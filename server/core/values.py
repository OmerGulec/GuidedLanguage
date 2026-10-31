from datetime import datetime

from core.memory import recall
from core.settings import Settings
from core.state import CardState


def value(card: CardState | None, at: datetime, settings: Settings) -> float:
    if card is None or not card.passed:
        return 0.0
    chance = recall(card.memory, at, settings)
    return 1.0 if chance >= settings.retention else chance
