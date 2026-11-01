import bz2
import urllib.request
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping, Sequence, Set
from datetime import UTC, datetime
from pathlib import Path

from core.pack import GrammarItem, Occurrence, Passage, Source, Word, passage_id
from langs.ja.analyser import Analyser, Lexicon, Link, Token, read_readings, word
from langs.ja.checks import check_links
from langs.ja.dictionary import read_jmdict
from langs.ja.grammar import Found, Grammar, read_rules
from pipeline import grammar as grammar_rules
from pipeline.labels import SAMPLES, Place, read_agreed
from pipeline.lessons import GRAMMAR, Lesson, read_lessons
from pipeline.splits import SPLITS, read_splits, split
from store.pack import write_pack
from store.paths import CONTENT, DATA, PACK
from store.texts import Page, write_texts

JMDICT_URL = "https://www.edrdg.org/pub/Nihongo/JMdict_e.gz"
TATOEBA_URL = "https://downloads.tatoeba.org/exports/per_language/jpn/jpn_sentences.tsv.bz2"
ENGLISH_URL = "https://downloads.tatoeba.org/exports/per_language/eng/eng_sentences.tsv.bz2"
LINKS_URL = "https://downloads.tatoeba.org/exports/per_language/jpn/jpn-eng_links.tsv.bz2"
TATOEBA = Source("tatoeba", "Tatoeba", "CC BY 2.0 FR", "full")
UNRESOLVED_SHOWN = 15
WORDS_SHOWN = 20


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


def tatoeba_links(path: Path) -> Iterator[tuple[int, int]]:
    with bz2.open(path, "rt", encoding="utf-8") as lines:
        for line in lines:
            source, target = line.split("\t")
            yield int(source), int(target)


def translations(
    links: Iterable[tuple[int, int]], sentences: Iterable[tuple[int, str]], wanted: Set[int]
) -> dict[int, str]:
    """One translation per wanted sentence: the oldest, which has had the most readers."""
    chosen: dict[int, int] = {}
    for sentence, translation in links:
        if sentence in wanted and (sentence not in chosen or translation < chosen[sentence]):
            chosen[sentence] = translation
    needed = set(chosen.values())
    texts = {number: text for number, text in sentences if number in needed}
    return {sentence: texts[t] for sentence, t in chosen.items() if t in texts}


def page(lesson: Lesson) -> Page:
    h = lesson.header
    return Page(lesson.id, h.kind, h.name, h.written, h.label, h.form, h.key, lesson.body)


def build() -> None:
    entries = list(read_jmdict(fetch(JMDICT_URL)))
    lexicon = Lexicon(entries, read_readings(CONTENT / "readings.tsv"))
    analyser = Analyser()
    grammar = Grammar(read_rules(grammar_rules.RULES))
    weights = read_splits(SPLITS)
    labels = read_agreed(SAMPLES)
    lessons = read_lessons(GRAMMAR).values()
    graph = [
        GrammarItem(i.id, i.header.kind, tuple(i.prerequisites), i.header.nuance)
        for i in lessons
        if i.header.kind != "form"
    ]
    words = {w.id: w for w in map(word, entries)}
    unresolved: set[str] = set()
    passages: dict[str, Passage] = {}
    occurrences: list[Occurrence] = []
    for number, text in tatoeba_sentences(fetch(TATOEBA_URL)):
        pid = passage_id(TATOEBA.id, text)
        if pid in passages:
            continue
        passages[pid] = Passage(pid, TATOEBA.id, number, text)
        tokens = analyser.tokens(text)
        forms = [form for form in grammar.find(tokens) if form.uses]
        for token, link in words_outside(forms, tokens, lexicon):
            if link.item not in words:
                words[link.item] = lexicon.unresolved(token)
                unresolved.add(link.item)
            occurrences.append(
                Occurrence(pid, link.item, link.spelling, link.phonetic, token.start, token.end, 1)
            )
        occurrences += grammar_occurrences(pid, text, forms, weights, labels)
    meta = {
        "built": datetime.now(UTC).isoformat(timespec="seconds"),
        "analyser": "fugashi + unidic-lite",
        "dictionary": "JMdict_e",
    }
    write_pack(PACK, meta, [TATOEBA], words.values(), graph, passages.values(), occurrences)
    english = translations(
        tatoeba_links(fetch(LINKS_URL)),
        tatoeba_sentences(fetch(ENGLISH_URL)),
        {p.position for p in passages.values()},
    )
    write_texts(
        PACK,
        {p.id: english[p.position] for p in passages.values() if p.position in english},
        {word(entry).id: entry.senses for entry in entries},
        map(page, lessons),
    )
    report(words, unresolved, len(passages), occurrences)
    print(f"written {PACK}")

    failures = check_links(analyser, lexicon, CONTENT / "link-checks.tsv")
    failures += grammar_rules.check()
    for failure in failures:
        print(f"check failed: {failure}")
    if failures:
        raise SystemExit(1)


def words_outside(
    forms: Iterable[Found], tokens: Sequence[Token], lexicon: Lexicon
) -> Iterator[tuple[Token, Link]]:
    """Each word with its link, less those that are part of a grammar form (こと and できる in
    ことができる). A word a form only frames stays a word (待つ in お待ちになる)."""
    taken = [(tokens[i].start, tokens[i].end) for f in forms for i in f.tokens if i not in f.words]
    for token, entry in lexicon.words(tokens):
        if not any(start < token.end and token.start < end for start, end in taken):
            yield token, lexicon.link(token, entry)


def grammar_occurrences(
    passage: str,
    text: str,
    forms: Iterable[Found],
    weights: Mapping[str, float],
    labels: Mapping[Place, str],
) -> Iterator[Occurrence]:
    """Each use a form may have, with its probability: its label's use where two models agree,
    and elsewhere, until the model pass labels every passage, the shares measured on a sample
    (006)."""
    for form in forms:
        spelling = text[form.start : form.end]
        label = labels.get((passage, form.start))
        uses = {label: 1.0} if label in form.uses else split(form.uses, weights)
        for use, share in uses.items():
            yield Occurrence(passage, use, spelling, True, form.start, form.end, share)


def report(
    words: dict[str, Word], unresolved: set[str], passages: int, occurrences: list[Occurrence]
) -> None:
    in_words = [o for o in occurrences if o.item in words]
    linked = sum(o.item not in unresolved for o in in_words)
    print(f"{passages} passages, {len(in_words)} word occurrences")
    print(f"linked to JMdict: {linked / len(in_words):.1%}")
    print(f"grammar occurrences: {len(occurrences) - len(in_words)}")

    passages_per_item = Counter(item for _, item in {(o.passage, o.item) for o in in_words})
    ranked = [item for item, _ in passages_per_item.most_common()]

    top_unresolved = [item for item in ranked if item in unresolved][:UNRESOLVED_SHOWN]
    print("most frequent unresolved:", " ".join(label(words[item]) for item in top_unresolved))

    print("most frequent words:")
    for item in ranked[:WORDS_SHOWN]:
        word = words[item]
        print(f"  {passages_per_item[item]:>6}  {label(word)}  {'; '.join(word.glosses)}")


def label(word: Word) -> str:
    return word.spellings[0] if word.spellings else word.readings[0]


if __name__ == "__main__":
    build()
