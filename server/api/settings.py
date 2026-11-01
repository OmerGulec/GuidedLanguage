"""The learner's settings (You): the study day, daily amounts and how the reader looks."""

from collections.abc import Callable
from dataclasses import replace
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, available_timezones

from fastapi import APIRouter, Depends
from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from api.server import Server
from core.settings import Settings
from store.settings import read_settings, write_settings

HOURS_IN_DAY = 24
_DEFAULTS = Settings()


def _zone(name: str) -> str:
    if name not in available_timezones():
        raise ValueError(f"unknown time zone {name}")
    return name


class LearnerSettings(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    zone: Annotated[str, AfterValidator(_zone)] = "UTC"
    day_start_hour: Annotated[int, Field(ge=0, lt=HOURS_IN_DAY)] = _DEFAULTS.day_start_hour
    new_budget: Annotated[int, Field(ge=0)] = _DEFAULTS.new_budget
    grammar_cap: Annotated[int, Field(ge=0)] = _DEFAULTS.grammar_cap
    review_cap: Annotated[int, Field(ge=0)] = _DEFAULTS.review_cap
    reading_per_day: Annotated[int, Field(ge=0)] = _DEFAULTS.reading_per_day
    # Readings printed over the text: never, over words not yet known, or over every word
    # written in kanji. A tap is a lookup either way.
    readings: Literal["off", "unknown", "kanji"] = "off"


def learner_settings(server: Server, account: int) -> LearnerSettings:
    stored = read_settings(server.db, account)
    return LearnerSettings() if stored is None else LearnerSettings.model_validate_json(stored)


def core_settings(settings: LearnerSettings) -> Settings:
    return replace(
        Settings(),
        zone=ZoneInfo(settings.zone),
        day_start_hour=settings.day_start_hour,
        new_budget=settings.new_budget,
        grammar_cap=settings.grammar_cap,
        review_cap=settings.review_cap,
        reading_per_day=settings.reading_per_day,
    )


def routes(server: Server, signed_in: Callable[..., int]) -> APIRouter:
    router = APIRouter(prefix="/api/settings")

    @router.get("")
    def get(account: Annotated[int, Depends(signed_in)]) -> LearnerSettings:
        return learner_settings(server, account)

    @router.put("")
    def put(body: LearnerSettings, account: Annotated[int, Depends(signed_in)]) -> LearnerSettings:
        write_settings(server.db, account, body.model_dump_json())
        # Derivation applies the current settings to the whole history (013).
        server.learners.forget(account)
        return body

    return router
