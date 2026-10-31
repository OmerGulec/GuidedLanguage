from datetime import datetime, timedelta
from itertools import count
from zoneinfo import ZoneInfo

from core.events import Event, Payload
from core.settings import Settings

TOKYO = Settings(zone=ZoneInfo("Asia/Tokyo"))
_ids = count()


def at(day: int, hour: int) -> datetime:
    return datetime(2026, 11, 1, hour, tzinfo=TOKYO.zone) + timedelta(days=day - 1)


def event(when: datetime, payload: Payload) -> Event:
    return Event(f"e{next(_ids)}", when, "ours", payload)
