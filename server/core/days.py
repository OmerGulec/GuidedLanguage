from datetime import date, datetime, time, timedelta

from core.settings import Settings


def study_day(at: datetime, settings: Settings) -> date:
    local = at.astimezone(settings.zone)
    return (local - timedelta(hours=settings.day_start_hour)).date()


def next_boundary(at: datetime, settings: Settings) -> datetime:
    tomorrow = study_day(at, settings) + timedelta(days=1)
    return datetime.combine(tomorrow, time(settings.day_start_hour), tzinfo=settings.zone)
