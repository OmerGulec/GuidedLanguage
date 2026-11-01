from dataclasses import dataclass
from datetime import datetime
from typing import Literal

type Modality = Literal["reading", "listening"]


@dataclass(frozen=True, slots=True)
class Introduced:
    item: str
    reason: Literal["new", "reteach", "explanation", "import"]


@dataclass(frozen=True, slots=True)
class Reviewed:
    card: str
    passed: bool
    # "import": answered in another app, which did not record how.
    method: Literal["self", "typed", "choice", "import"]
    answer: str | None = None


@dataclass(frozen=True, slots=True)
class LookedUp:
    item: str
    passage: str
    surface: str
    context: str


@dataclass(frozen=True, slots=True)
class Read:
    passage: str
    modality: Modality


@dataclass(frozen=True, slots=True)
class Exercised:
    passage: str
    kind: Literal["dictation", "question"]
    passed: bool
    items: tuple[str, ...]
    answer: str | None = None


@dataclass(frozen=True, slots=True)
class Missed:
    item: str
    passage: str
    surface: str
    context: str


@dataclass(frozen=True, slots=True)
class Marked:
    item: str
    status: Literal["known", "ignored", "unknown"]
    # placement: passed in the reading check; course: from a course table (014).
    reason: Literal["hand", "placement", "course", "import"]


@dataclass(frozen=True, slots=True)
class Retracted:
    event: str


type Payload = Introduced | Reviewed | LookedUp | Read | Exercised | Missed | Marked | Retracted


@dataclass(frozen=True, slots=True)
class Event:
    id: str
    at: datetime
    origin: str
    payload: Payload
