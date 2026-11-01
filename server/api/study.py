"""The study session (Review): one step at a time, in the plan's order (005, 013).

The client shows a step, posts what happened as events and asks for the next; it holds no
learning logic (003). A step is one member of a closed union, so a new kind of step, such as an
explanation step or a listening card, is a new member that every handler must take.
"""

from collections.abc import Callable
from typing import Annotated, Literal

import numpy as np
from fastapi import APIRouter, Depends
from numpy.typing import NDArray
from pydantic import BaseModel, Field

from api.library import GrammarView, Library, PassageView, WordView, item_view, passage_view
from api.server import Server
from api.settings import core_settings, learner_settings
from core.cards import Card, Goal
from core.days import next_boundary
from core.passages import card_passages
from core.plan import Plan, Situation, plan
from core.state import State
from core.unknowns import unknowns
from core.values import values

# v1 has the Reader goal only (docs/v1.md); other goals arrive as a setting.
GOAL: Goal = "reader"


class CardStep(BaseModel):
    kind: Literal["card"] = "card"
    card: str
    rung: str
    # What the card shows of a word: its spelling, or its reading for a word learned in kana.
    spelling: str | None
    item: WordView | GrammarView
    passage: PassageView | None
    # A grammar card marks its form until the card graduates (004).
    marked: bool


class PageStep(BaseModel):
    kind: Literal["page"] = "page"
    reason: Literal["new", "reteach"]
    item: WordView | GrammarView


class MeetingStep(BaseModel):
    """A new word met in a passage where it is the only unknown, where the library allows (004)."""

    kind: Literal["meeting"] = "meeting"
    spelling: str
    item: WordView
    passage: PassageView | None


class DoneStep(BaseModel):
    kind: Literal["done"] = "done"


type Step = Annotated[CardStep | PageStep | MeetingStep | DoneStep, Field(discriminator="kind")]


def routes(server: Server, library: Library, signed_in: Callable[..., int]) -> APIRouter:
    router = APIRouter(prefix="/api/study")

    @router.get("/next")
    def next_step(
        account: Annotated[int, Depends(signed_in)], sound: bool = False, keyboard: bool = False
    ) -> Step:
        settings = core_settings(learner_settings(server, account))
        state = server.learners.state(account, settings)
        now = server.clock()
        reading = values(state, library.pack, settings, next_boundary(now, settings), "reading")
        unknown = unknowns(reading, library.pack)
        today = plan(
            state,
            {"reading": unknown},
            library.pack,
            library.ranking,
            GOAL,
            Situation(sound, keyboard),
            settings,
            now,
        )
        return _next(today, state, library, reading, unknown)

    return router


def _next(
    today: Plan,
    state: State,
    library: Library,
    reading: NDArray[np.float64],
    unknown: NDArray[np.float64],
) -> CardStep | PageStep | MeetingStep | DoneStep:
    def passage_of(card: str) -> PassageView | None:
        chosen = card_passages([card], state, reading, unknown, library.pack, library.eligible)
        passage = chosen[card]
        return None if passage is None else passage_view(library, passage, state, reading)

    def card_step(card: str) -> CardStep:
        parsed = Card.parse(card)
        held = state.cards.get(card)
        view = _view(library, parsed.items[0])
        grammar = isinstance(view, GrammarView)
        return CardStep(
            card=card,
            rung=parsed.rung,
            spelling=None if isinstance(view, GrammarView) else _spelling(parsed, view),
            item=view,
            passage=passage_of(card),
            marked=grammar and (held is None or not held.graduated),
        )

    if today.reviews:
        return card_step(today.reviews[0])
    if today.reteach:
        return PageStep(reason="reteach", item=_view(library, today.reteach[0]))
    if today.new:
        offer = today.new[0]
        # A system has no cards and is offered by its item id (013).
        if offer in library.pack.grammar:
            return PageStep(reason="new", item=_view(library, offer))
        item = Card.parse(offer).items[0]
        if item in state.introduced:
            return card_step(offer)
        view = _view(library, item)
        if isinstance(view, GrammarView):
            return PageStep(reason="new", item=view)
        return MeetingStep(
            spelling=_spelling(Card.parse(offer), view), item=view, passage=passage_of(offer)
        )
    if today.later:
        return card_step(today.later[0])
    return DoneStep()


def _spelling(card: Card, word: WordView) -> str:
    return card.spelling or word.readings[0]


def _view(library: Library, item: str) -> WordView | GrammarView:
    view = item_view(library, item)
    assert view is not None, f"the plan offered {item}, which the pack lacks"
    return view
