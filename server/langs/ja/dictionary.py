import gzip
import io
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

COMMON_TAGS = frozenset({"news1", "ichi1", "spec1", "spec2", "gai1"})
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
    priorities = {p.text for p in element.iterfind("k_ele/ke_pri")}
    priorities |= {p.text for p in element.iterfind("r_ele/re_pri")}
    first_sense = element.find("sense")
    return Entry(
        id=int(element.findtext("ent_seq", "0")),
        spellings=tuple(k.text or "" for k in element.iterfind("k_ele/keb")),
        readings=tuple(r.text or "" for r in element.iterfind("r_ele/reb")),
        glosses=()
        if first_sense is None
        else tuple(g.text or "" for g in first_sense.iterfind("gloss")),
        parts_of_speech=frozenset(p.text or "" for p in element.iterfind("sense/pos")),
        common=bool(priorities & COMMON_TAGS),
    )
