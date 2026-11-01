from dataclasses import dataclass
from zoneinfo import ZoneInfo

from fsrs.scheduler import DEFAULT_PARAMETERS

UTC = ZoneInfo("UTC")
FSRS_PARAMETERS = tuple(DEFAULT_PARAMETERS)


@dataclass(frozen=True, slots=True)
class Settings:
    zone: ZoneInfo = UTC
    day_start_hour: int = 4
    retention: float = 0.9
    scheduler_parameters: tuple[float, ...] = FSRS_PARAMETERS
    lapses_before_suspension: int = 8
    marked_stability_days: float = 60
    marked_spread_days: float = 60
    new_budget: int = 10
    # Grammar uses, formations and systems a day, within the new budget (009).
    grammar_cap: int = 2
    # Rank is frequency over effort (009): a grammar use takes longer to learn than a word.
    word_effort: float = 1.0
    grammar_effort: float = 3.0
    # Marks nobody has checked come up for review within this many days (014).
    doubtful_review_days: float = 21
    review_cap: int = 200
    reading_per_day: int = 3
    spacing_days: int = 3
