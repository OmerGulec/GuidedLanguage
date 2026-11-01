"""Today (005): the day's work as numbered steps, with what is left and what is done."""

from collections.abc import Callable
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.library import Library
from api.server import Server
from api.study import planned
from core.days import study_day
from core.plan import Situation


class Today(BaseModel):
    day: date
    # Left: reviews (learning steps due later included), new items, passages to read.
    reviews: int
    new: int
    reading: int
    # Done today: cards answered and items met.
    reviewed: int
    met: int


def routes(server: Server, library: Library, signed_in: Callable[..., int]) -> APIRouter:
    router = APIRouter(prefix="/api/today")

    @router.get("")
    def today(
        account: Annotated[int, Depends(signed_in)], sound: bool = False, keyboard: bool = False
    ) -> Today:
        day = planned(server, library, account, Situation(sound, keyboard))
        when = study_day(server.clock(), day.settings)

        return Today(
            day=when,
            reviews=len(day.plan.reviews) + len(day.plan.later),
            new=len(day.plan.new) + len(day.plan.reteach),
            reading=sum(len(passages) for passages in day.plan.passages.values()),
            reviewed=sum(
                study_day(held.memory.last_review, day.settings) == when
                for held in day.state.cards.values()
            ),
            met=sum(study_day(at, day.settings) == when for at in day.state.introduced.values()),
        )

    return router
