from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

import fugashi  # pyright: ignore[reportMissingTypeStubs]

from core.pack import Word
from langs.ja.content import rows
from langs.ja.dictionary import Entry

# UniDic part of speech → JMdict part-of-speech prefixes it may link to.
WORD_PARTS_OF_SPEECH: dict[str, tuple[str, ...]] = {
    "名詞": ("n",),
    "動詞": ("v",),
    "形容詞": ("adj-i",),
    "形状詞": ("adj-na", "adj-no"),
    "副詞": ("adv",),
    "代名詞": ("pn",),
    "連体詞": ("adj-pn",),
    "接続詞": ("conj",),
    "感動詞": ("int",),
    "接頭辞": ("pref",),
    "接尾辞": ("suf", "n-suf", "ctr"),
}
# Names and numbers never count as unknown (013), so they produce no occurrence.
FREE_SUBTYPES = frozenset({"固有名詞", "数詞"})


class _Features(Protocol):
    pos1: str
    pos2: str
    lemma: str | None
    lForm: str | None  # noqa: N815
    kanaBase: str | None  # noqa: N815
    orthBase: str | None  # noqa: N815


class _Node(Protocol):
    surface: str
    white_space: str
    feature: _Features


@dataclass(frozen=True, slots=True)
class Token:
    surface: str
    lemma: str
    base: str
    # The dictionary form's reading, and the reading of the dictionary form as written here.
    # They differ for a potential verb (会える under 会う) or a variant reading (いい under 良い).
    reading: str
    written_reading: str
    part_of_speech: str
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class Link:
    item: str
    spelling: str
    phonetic: bool


def word(entry: Entry) -> Word:
    return Word(f"w:{entry.id}", entry.spellings, entry.readings, entry.glosses, entry.common)


_KATAKANA_TO_HIRAGANA = ord("ア") - ord("あ")


def hiragana(text: str) -> str:
    return "".join(chr(ord(c) - _KATAKANA_TO_HIRAGANA) if "ァ" <= c <= "ヶ" else c for c in text)


def is_kana(text: str) -> bool:
    return all("ぁ" <= c <= "ゖ" or "ァ" <= c <= "ヺ" or c == "ー" for c in text)


class _Tagger(Protocol):
    def __call__(self, text: str) -> list[_Node]: ...


class Analyser:
    def __init__(self) -> None:
        self._tagger = cast(_Tagger, fugashi.Tagger())  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

    def words(self, text: str) -> Iterator[Token]:
        position = 0
        for node in self._tagger(text):
            start = position + len(node.white_space)
            position = start + len(node.surface)
            f = node.feature
            if f.pos1 not in WORD_PARTS_OF_SPEECH or f.pos2 in FREE_SUBTYPES:
                continue
            # UniDic lemmas may carry a disambiguating suffix, as in 私-代名詞 or コーヒー-coffee.
            lemma = (f.lemma or node.surface).split("-")[0]
            yield Token(
                surface=node.surface,
                lemma=lemma,
                base=f.orthBase or node.surface,
                reading=hiragana(f.lForm or node.surface),
                written_reading=hiragana(f.kanaBase or node.surface),
                part_of_speech=f.pos1,
                start=start,
                end=position,
            )


def read_readings(path: Path) -> dict[tuple[str, str], str]:
    return {(lemma, analysed): usual for lemma, analysed, usual in rows(path)}


class Lexicon:
    def __init__(self, entries: Iterable[Entry], readings: Mapping[tuple[str, str], str]) -> None:
        self._readings = readings
        self._by_form: dict[str, list[Entry]] = defaultdict(list)
        for entry in entries:
            for form in {*entry.spellings, *map(hiragana, entry.readings)}:
                self._by_form[form].append(entry)

    def readings(self, token: Token) -> tuple[str, ...]:
        """A word written in kana is matched by how it is written first, then by its lemma."""
        lemma_reading = self._readings.get((token.lemma, token.reading), token.reading)
        if is_kana(token.surface) and token.written_reading != lemma_reading:
            return (token.written_reading, lemma_reading)
        return (lemma_reading,)

    def entry(self, token: Token) -> Entry | None:
        # The lemma (居る for いる, 事 for こと) is the analyser's strongest evidence. Matching kana
        # forms first would pick whichever entry shares the reading and has the lowest id.
        for reading in self.readings(token):
            for forms in ((token.lemma,), (token.base, token.surface)):
                found = {e.id: e for f in forms for e in self._by_form.get(hiragana(f), ())}
                heard = [e for e in found.values() if reading in map(hiragana, e.readings)]
                if heard:
                    return self._best(heard, token)
        return None

    def _best(self, entries: list[Entry], token: Token) -> Entry:
        prefixes = WORD_PARTS_OF_SPEECH[token.part_of_speech]
        fitting = [e for e in entries if any(p.startswith(prefixes) for p in e.parts_of_speech)]
        return min(fitting or entries, key=lambda e: (not e.common, e.id))

    def link(self, token: Token) -> Link:
        phonetic = is_kana(token.surface)
        entry = self.entry(token)
        if entry is None:
            return Link(self.unresolved(token).id, token.base, phonetic)
        if phonetic:
            readings = self.readings(token)
            spelling = next((r for r in entry.readings if hiragana(r) in readings), token.base)
        else:
            spelling = token.base if token.base in entry.spellings else token.lemma
        return Link(word(entry).id, spelling, phonetic)

    def unresolved(self, token: Token) -> Word:
        item = f"u:{token.lemma}/{token.reading}"
        return Word(item, (token.base,), (token.reading,), glosses=(), common=False)
