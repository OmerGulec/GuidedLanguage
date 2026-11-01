"""An app on the fixture pack with one account, for tests of the API."""

from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app
from store.accounts import create_account
from store.database import open_database
from tests.history import at
from tests.packs import FIXTURE

NOW = at(1, 9)
OWNER = {"email": "owner@example.com", "password": "kana and kanji"}


def owner_database(folder: Path) -> Path:
    path = folder / "users.sqlite"
    create_account(open_database(path), OWNER["email"], OWNER["password"], NOW)
    return path


def app_client(users: Path) -> TestClient:
    """A client of the app at a fixed instant, not yet signed in."""
    return TestClient(create_app(users, FIXTURE, clock=lambda: NOW))
