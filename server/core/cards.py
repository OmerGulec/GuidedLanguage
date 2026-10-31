from dataclasses import dataclass
from typing import Literal

type Goal = Literal["reader", "listener", "kanji", "complete"]
type LadderKind = Literal[
    "kana", "word", "phrase", "grammar", "formation", "kanji", "kanji reading", "contrast"
]


@dataclass(frozen=True, slots=True)
class Rung:
    name: str
    goals: frozenset[Goal]
    needs_sound: bool = False
    needs_keyboard: bool = False


_ALL: frozenset[Goal] = frozenset({"reader", "listener", "kanji", "complete"})
_LISTENING: frozenset[Goal] = frozenset({"listener", "complete"})
_KANJI: frozenset[Goal] = frozenset({"kanji", "complete"})
_COMPLETE: frozenset[Goal] = frozenset({"complete"})
_WORD = (
    Rung("recognize", _ALL),
    Rung("listen", _LISTENING, needs_sound=True),
    Rung("cloze", _COMPLETE, needs_keyboard=True),
    Rung("pitch", _COMPLETE, needs_sound=True),
)

LADDERS: dict[LadderKind, tuple[Rung, ...]] = {
    "kana": (Rung("read", _ALL), Rung("hear", _LISTENING, needs_sound=True)),
    "word": _WORD,
    "phrase": _WORD,
    "grammar": (Rung("sentence", _ALL), Rung("cloze", _COMPLETE, needs_keyboard=True)),
    "formation": (Rung("undo", _ALL), Rung("build", _COMPLETE, needs_keyboard=True)),
    "kanji": (Rung("meaning", _KANJI),),
    "kanji reading": (Rung("reading", _KANJI),),
    "contrast": (Rung("contrast", _ALL),),
}
FIRST_RUNGS = frozenset(ladder[0].name for ladder in LADDERS.values())
RUNGS = {rung.name: rung for ladder in LADDERS.values() for rung in ladder}


def ladder(kind: LadderKind, goal: Goal) -> tuple[Rung, ...]:
    return tuple(rung for rung in LADDERS[kind] if goal in rung.goals)


@dataclass(frozen=True, slots=True)
class Card:
    items: tuple[str, ...]
    spelling: str | None
    rung: str

    @property
    def id(self) -> str:
        subject = "+".join(self.items)
        if self.spelling is not None:
            subject += f"@{self.spelling}"
        return f"{subject}/{self.rung}"

    @staticmethod
    def parse(card_id: str) -> "Card":
        subject, rung = card_id.rsplit("/", 1)
        items, _, spelling = subject.partition("@")
        return Card(tuple(items.split("+")), spelling or None, rung)
