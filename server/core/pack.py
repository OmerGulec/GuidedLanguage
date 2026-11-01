import hashlib
import unicodedata
from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

type Display = Literal["full", "excerpt", "analysis"]

PASSAGE_ID_LENGTH = 16


@dataclass(frozen=True, slots=True)
class Source:
    id: str
    name: str
    license: str
    display: Display


@dataclass(frozen=True, slots=True)
class Word:
    id: str
    spellings: tuple[str, ...]
    readings: tuple[str, ...]
    glosses: tuple[str, ...]
    common: bool


@dataclass(frozen=True, slots=True)
class GrammarUse:
    id: str
    # Nuance never counts as unknown (007).
    nuance: bool


@dataclass(frozen=True, slots=True)
class Passage:
    id: str
    source: str
    position: int
    text: str


@dataclass(frozen=True, slots=True)
class Occurrence:
    passage: str
    item: str
    spelling: str
    phonetic: bool
    start: int
    end: int
    # That the item is the one meant here: 1 for a word; for a grammar use, its share of the
    # form found at this span (006).
    probability: float


def passage_id(source: str, text: str) -> str:
    normalised = unicodedata.normalize("NFKC", text).strip()
    return hashlib.sha256(f"{source}\n{normalised}".encode()).hexdigest()[:PASSAGE_ID_LENGTH]


@dataclass(frozen=True, slots=True)
class Column:
    item: str
    # None when the spelling writes the sound directly: any card linking sound and meaning counts.
    spelling: str | None


@dataclass(frozen=True, slots=True, eq=False)
class Pack:
    passages: tuple[str, ...]
    sources: tuple[str, ...]
    passage_sources: NDArray[np.int32]
    columns: tuple[Column, ...]
    # Each appearance is one column present in one passage, at most once per passage, with the
    # highest probability it has there.
    appearance_passages: NDArray[np.int32]
    appearance_columns: NDArray[np.int32]
    appearance_probabilities: NDArray[np.float64]
    grammar: frozenset[str]
    nuance: frozenset[str]
