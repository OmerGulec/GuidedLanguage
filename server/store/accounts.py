"""Accounts and their sign-in sessions (011)."""

import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

SESSION_LENGTH = timedelta(days=90)
TOKEN_BYTES = 32

_hasher = PasswordHasher()


def create_account(db: sqlite3.Connection, email: str, password: str, now: datetime) -> int | None:
    """The new account's id, or None when the email already has one."""
    try:
        cursor = db.execute(
            "INSERT INTO accounts (email, password, created) VALUES (?, ?, ?)",
            (_normal(email), _hasher.hash(password), now.isoformat()),
        )
    except sqlite3.IntegrityError:
        return None
    assert cursor.lastrowid is not None
    return cursor.lastrowid


def sign_in(db: sqlite3.Connection, email: str, password: str, now: datetime) -> str | None:
    """A new session's token, or None when the email or password is wrong."""
    row = db.execute(
        "SELECT id, password FROM accounts WHERE email = ?", (_normal(email),)
    ).fetchone()
    if row is None:
        return None
    account, stored = row
    try:
        _hasher.verify(stored, password)
    except VerificationError:
        return None
    token = secrets.token_urlsafe(TOKEN_BYTES)
    db.execute(
        "INSERT INTO sessions VALUES (?, ?, ?)",
        (_digest(token), account, (now + SESSION_LENGTH).isoformat()),
    )
    return token


def account_of(db: sqlite3.Connection, token: str, now: datetime) -> int | None:
    row = db.execute(
        "SELECT account, expires FROM sessions WHERE token = ?", (_digest(token),)
    ).fetchone()
    if row is None or datetime.fromisoformat(row[1]) <= now:
        return None
    return row[0]


def sign_out(db: sqlite3.Connection, token: str) -> None:
    db.execute("DELETE FROM sessions WHERE token = ?", (_digest(token),))


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _normal(email: str) -> str:
    return email.strip().lower()
