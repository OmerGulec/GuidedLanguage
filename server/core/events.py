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
    method: Literal["self", "typed", "choice"]
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
    reason: Literal["hand", "placement", "import"]


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
