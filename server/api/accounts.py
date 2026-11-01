"""Making an account: `uv run python -m api.accounts EMAIL` asks for its password. v1 has no
sign-up page."""

import sys
from getpass import getpass

from api.app import now
from store.accounts import create_account
from store.database import open_database
from store.paths import USERS

if __name__ == "__main__":
    match sys.argv[1:]:
        case [email]:
            account = create_account(open_database(USERS), email, getpass("Password: "), now())
            print("that email already has an account" if account is None else f"account {account}")
        case _:
            raise SystemExit("usage: api.accounts EMAIL")
