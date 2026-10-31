import hashlib
import unicodedata
from dataclasses import dataclass
from typing import Literal

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


def passage_id(source: str, text: str) -> str:
    normalised = unicodedata.normalize("NFKC", text).strip()
    return hashlib.sha256(f"{source}\n{normalised}".encode()).hexdigest()[:PASSAGE_ID_LENGTH]
