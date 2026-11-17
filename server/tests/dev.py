"""The development server: the app as a named learner (012).

`uv run python -m tests.dev LEARNER [PORT [PACK]]` simulates the learner into a fresh user
database, with their history ending yesterday, and serves the app on the real pack unless another
is named. Sign in with the email and password it prints.
"""

import sys
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import uvicorn

from api.app import create_app, now
from api.web import BUILD
from core.candidates import Ranking, ranking
from core.events import Event
from core.pack import Pack
from core.settings import Settings
from sim.learner import Simulation
from sim.learners import day_zero, heavy_user, importer, three_months
from store.accounts import create_account
from store.database import open_database
from store.events import append
from store.pack import read_eligible, read_pack
from store.paths import DATA, PACK

LEARNERS: dict[str, Callable[[Pack, Ranking, Settings], Simulation]] = {
    "day-zero": day_zero,
    "importer": importer,
    "three-months": three_months,
    "heavy-user": heavy_user,
}
EMAIL = "learner@example.com"
PASSWORD = "learner"
DEFAULT_PORT = 8000
EVERY_ADDRESS = "0.0.0.0"
USAGE = f"usage: python -m tests.dev {{{','.join(LEARNERS)}}} [PORT [PACK]]"


def ending_yesterday(events: list[Event], today: datetime) -> list[Event]:
    """The same history, moved by whole days so that its last day is the day before today."""
    if not events:
        return []
    last = max(event.at for event in events)
    days = (today.date() - last.astimezone(UTC).date()).days - 1
    return [replace(event, at=event.at + timedelta(days=days)) for event in events]


def learner_database(name: str, pack: Path, folder: Path, today: datetime) -> Path:
    """A fresh user database holding one account with the named learner's history."""
    settings = Settings()
    read = read_pack(pack)
    simulation = LEARNERS[name](read, ranking(read, settings, read_eligible(pack)), settings)

    path = folder / f"{name}.sqlite"
    for stale in folder.glob(f"{name}.sqlite*"):
        stale.unlink()
    db = open_database(path)
    account = create_account(db, EMAIL, PASSWORD, today)
    assert account is not None
    append(db, account, ending_yesterday(simulation.events, today), today)
    db.close()
    return path


if __name__ == "__main__":
    match sys.argv[1:]:
        case [name] if name in LEARNERS:
            port, pack = DEFAULT_PORT, PACK
        case [name, number] if name in LEARNERS and number.isdigit():
            port, pack = int(number), PACK
        case [name, number, path] if name in LEARNERS and number.isdigit():
            port, pack = int(number), Path(path)
        case _:
            raise SystemExit(USAGE)

    users = learner_database(name, pack, DATA / "dev", now())
    print(f"{name}: sign in as {EMAIL} with the password {PASSWORD}", flush=True)
    built_web = BUILD if BUILD.is_dir() else None
    uvicorn.run(create_app(users, pack, now, built_web=built_web), host=EVERY_ADDRESS, port=port)
