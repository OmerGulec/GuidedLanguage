"""The server: one process serving the API, and later the built web app (011)."""

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI

from api import events, session
from api.learners import Learners
from api.server import Server
from store.database import open_database


def create_app(users: Path, clock: Callable[[], datetime], secure_cookies: bool = False) -> FastAPI:
    db = open_database(users)
    server = Server(db, Learners(db), clock, secure_cookies)
    signed_in = session.signed_in(server)

    app = FastAPI(title="GuidedLanguage")
    app.include_router(session.routes(server))
    app.include_router(events.routes(server, signed_in))
    return app


def now() -> datetime:
    return datetime.now(UTC)
