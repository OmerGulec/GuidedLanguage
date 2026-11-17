"""The API's schema, which the web app's types are generated from (003).

`uv run python -m api.schema PACK` prints it; the routes are the same whatever the pack.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from api.app import create_app


def schema(pack: Path) -> str:
    with TemporaryDirectory() as folder:
        app = create_app(Path(folder) / "users.sqlite", pack, clock=lambda: datetime.now(UTC))
        return json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    match sys.argv[1:]:
        case [pack]:
            sys.stdout.write(schema(Path(pack)))
        case _:
            raise SystemExit("usage: python -m api.schema PACK")
