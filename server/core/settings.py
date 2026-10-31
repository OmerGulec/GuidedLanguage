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
