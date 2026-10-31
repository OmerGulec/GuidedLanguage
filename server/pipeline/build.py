import bz2
import urllib.request
from collections import Counter
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from core.pack import Occurrence, Passage, Source, Word, passage_id
from langs.ja.analyser import Analyser, Lexicon, read_readings, word
from langs.ja.dictionary import read_jmdict
from store.pack import write_pack

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
CONTENT = ROOT / "content" / "ja"
JMDICT_URL = "https://www.edrdg.org/pub/Nihongo/JMdict_e.gz"
TATOEBA_URL = "https://downloads.tatoeba.org/exports/per_language/jpn/jpn_sentences.tsv.bz2"
TATOEBA = Source("tatoeba", "Tatoeba", "CC BY 2.0 FR", "full")


def fetch(url: str) -> Path:
    path = DATA / "sources" / url.rsplit("/", 1)[1]
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, path)
    return path


def tatoeba_sentences(path: Path) -> Iterator[tuple[int, str]]:
    with bz2.open(path, "rt", encoding="utf-8") as lines:
        for line in lines:
            number, _, text = line.rstrip("\n").split("\t", 2)
            yield int(number), text


def build() -> None:
    entries = list(read_jmdict(fetch(JMDICT_URL)))
    lexicon = Lexicon(entries, read_readings(CONTENT / "readings.tsv"))
    analyser = Analyser()
    words = {w.id: w for w in map(word, entries)}
    unresolved: set[str] = set()
    passages: dict[str, Passage] = {}
    occurrences: list[Occurrence] = []
    for number, text in tatoeba_sentences(fetch(TATOEBA_URL)):
        pid = passage_id(TATOEBA.id, text)
        if pid in passages:
            continue
        passages[pid] = Passage(pid, TATOEBA.id, number, text)
        for token in analyser.words(text):
            link = lexicon.link(token)
            if link.item not in words:
                words[link.item] = lexicon.unresolved(token)
                unresolved.add(link.item)
            occurrences.append(
                Occurrence(pid, link.item, link.spelling, link.phonetic, token.start, token.end)
            )
    meta = {
        "built": datetime.now(UTC).isoformat(timespec="seconds"),
        "analyser": "fugashi + unidic-lite",
        "dictionary": "JMdict_e",
    }
    path = DATA / "packs" / "ja" / "pack.sqlite"
    write_pack(path, meta, [TATOEBA], words.values(), passages.values(), occurrences)
    report(words, unresolved, len(passages), occurrences)
    print(f"written {path}")


def report(
    words: dict[str, Word], unresolved: set[str], passages: int, occurrences: list[Occurrence]
) -> None:
    linked = sum(o.item not in unresolved for o in occurrences)
    print(f"{passages} passages, {len(occurrences)} word occurrences")
    print(f"linked to JMdict: {linked / len(occurrences):.1%}")
    in_passages = Counter(item for _, item in {(o.passage, o.item) for o in occurrences})
    top = [i for i, _ in in_passages.most_common() if i in unresolved][:15]
    print("most frequent unresolved:", " ".join(words[i].spellings[0] for i in top))
    print("most frequent words:")
    for item, count in in_passages.most_common(20):
        w = words[item]
        print(f"  {count:>6}  {w.spellings[0] if w.spellings else w.readings[0]}  {w.glosses[:1]}")


if __name__ == "__main__":
    build()
