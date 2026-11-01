"""What every route shares: the user database, learners' states and the clock."""

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from api.learners import Learners


@dataclass(frozen=True, slots=True)
class Server:
    db: sqlite3.Connection
    learners: Learners
    # The time now; development moves it forward to show any day of a learner's path (012).
    clock: Callable[[], datetime]
    # Cookies go only over TLS once the server runs behind it; locally it does not.
    secure_cookies: bool
