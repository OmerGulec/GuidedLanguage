"""Running the server: `uv run python -m api [PORT]`.

It listens on every address of this computer, so a phone on the same network can reach it
(docs/v1.md: local hosting). Make an account first with `uv run python -m api.accounts EMAIL`,
and build the web app with `npm run build` in `web/`; without it only the API is served.
"""

import sys

import uvicorn

from api.app import create_app, now
from api.web import BUILD
from store.paths import PACK, USERS

EVERY_ADDRESS = "0.0.0.0"
DEFAULT_PORT = 8000

if __name__ == "__main__":
    match sys.argv[1:]:
        case []:
            port = DEFAULT_PORT
        case [number] if number.isdigit():
            port = int(number)
        case _:
            raise SystemExit("usage: python -m api [PORT]")
    built_web = BUILD if BUILD.is_dir() else None
    uvicorn.run(create_app(USERS, PACK, now, built_web=built_web), host=EVERY_ADDRESS, port=port)
