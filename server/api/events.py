"""Receiving learning events from the client (013)."""

from collections.abc import Callable
from datetime import timedelta
from typing import Annotated, Literal, assert_never

from fastapi import APIRouter, Depends
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from api.server import Server
from core import events as core
from core.events import Modality
from store.events import append

ORIGIN = "ours"
# Clocks drift; an instant further ahead than this is a wrong clock, not a fast answer.
LARGEST_LEAD = timedelta(minutes=1)


class _Payload(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)


class Introduced(_Payload):
    kind: Literal["introduced"]
    item: str
    reason: Literal["new", "reteach", "explanation"]
    passage: str | None = None


class Reviewed(_Payload):
    kind: Literal["reviewed"]
    card: str
    passed: bool
    method: Literal["self", "typed", "choice"]
    answer: str | None = None
    passage: str | None = None


class LookedUp(_Payload):
    kind: Literal["looked-up"]
    item: str
    passage: str
    surface: str
    context: str


class Read(_Payload):
    kind: Literal["read"]
    passage: str
    modality: Modality


class Missed(_Payload):
    kind: Literal["missed"]
    item: str
    passage: str
    surface: str
    context: str


class Marked(_Payload):
    kind: Literal["marked"]
    item: str
    status: Literal["known", "ignored", "unknown"]


class Retracted(_Payload):
    kind: Literal["retracted"]
    event: str


type Payload = Annotated[
    Introduced | Reviewed | LookedUp | Read | Missed | Marked | Retracted,
    Field(discriminator="kind"),
]


class Event(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    id: str
    # JSON carries instants as text, which strict mode alone would refuse.
    at: Annotated[AwareDatetime, Field(strict=False)]
    payload: Payload


class Received(BaseModel):
    added: int
    # Events whose instant is ahead of the server's clock: not kept, so the client can fix them.
    refused: list[str]


def routes(server: Server, signed_in: Callable[..., int]) -> APIRouter:
    router = APIRouter(prefix="/api/events")

    @router.post("")
    def receive(events: list[Event], account: Annotated[int, Depends(signed_in)]) -> Received:
        now = server.clock()
        ahead = {e.id for e in events if e.at > now + LARGEST_LEAD}
        kept = [
            core.Event(e.id, e.at, ORIGIN, _payload(e.payload)) for e in events if e.id not in ahead
        ]
        return Received(added=append(server.db, account, kept, now), refused=sorted(ahead))

    return router


def _payload(
    payload: Introduced | Reviewed | LookedUp | Read | Missed | Marked | Retracted,
) -> core.Payload:
    match payload:
        case Introduced(item=item, reason=reason, passage=passage):
            return core.Introduced(item, reason, passage)
        case Reviewed(card=card, passed=passed, method=method, answer=answer, passage=passage):
            return core.Reviewed(card, passed, method, answer, passage)
        case LookedUp(item=item, passage=passage, surface=surface, context=context):
            return core.LookedUp(item, passage, surface, context)
        case Read(passage=passage, modality=modality):
            return core.Read(passage, modality)
        case Missed(item=item, passage=passage, surface=surface, context=context):
            return core.Missed(item, passage, surface, context)
        case Marked(item=item, status=status):
            return core.Marked(item, status, "hand")
        case Retracted(event=event):
            return core.Retracted(event)
        case _:
            assert_never(payload)
