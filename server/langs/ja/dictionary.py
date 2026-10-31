import gzip
import io
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

COMMON_TAGS = frozenset({"news1", "ichi1", "spec1", "spec2", "gai1"})

# Paths inside a JMdict <entry>.
_ID = "ent_seq"
_SPELLINGS = "k_ele/keb"
_READINGS = "r_ele/reb"
_PRIORITIES = ("k_ele/ke_pri", "r_ele/re_pri")
_FIRST_SENSE_GLOSSES = "sense[1]/gloss"
_PARTS_OF_SPEECH = "sense/pos"

_ENTITY = re.compile(r"&([\w-]+);")
_XML_ENTITIES = frozenset({"amp", "lt", "gt", "quot", "apos"})


@dataclass(frozen=True, slots=True)
class Entry:
    id: int
    spellings: tuple[str, ...]
    readings: tuple[str, ...]
    glosses: tuple[str, ...]
    parts_of_speech: frozenset[str]
    common: bool


def read_jmdict(path: Path) -> Iterator[Entry]:
    raw = path.read_bytes()
    text = (gzip.decompress(raw) if path.suffix == ".gz" else raw).decode()
    # JMdict marks parts of speech with entities such as &v5k;. Keeping the entity name gives
    # a stable code instead of its English description, and makes the DTD unnecessary.
    text = _ENTITY.sub(lambda m: m[0] if m[1] in _XML_ENTITIES else m[1], text)
    for _, element in ET.iterparse(io.BytesIO(text.encode()), events=("end",)):
        if element.tag == "entry":
            yield _entry(element)
            element.clear()


def _entry(element: ET.Element) -> Entry:
    priorities = {tag for path in _PRIORITIES for tag in _texts(element, path)}
    return Entry(
        id=int(_texts(element, _ID)[0]),
        spellings=_texts(element, _SPELLINGS),
        readings=_texts(element, _READINGS),
        glosses=_texts(element, _FIRST_SENSE_GLOSSES),
        parts_of_speech=frozenset(_texts(element, _PARTS_OF_SPEECH)),
        common=bool(priorities & COMMON_TAGS),
    )


def _texts(element: ET.Element, path: str) -> tuple[str, ...]:
    return tuple(child.text for child in element.iterfind(path) if child.text)
