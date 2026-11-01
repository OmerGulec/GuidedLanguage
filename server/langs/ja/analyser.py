from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping, Sequence
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
NUMBER = "数詞"
VERB = "動詞"
LOWER_ICHIDAN = "下一段"
# Names and numbers never count as unknown (013), so they produce no occurrence.
FREE_SUBTYPES = frozenset({"固有名詞", NUMBER})
# JMdict's expressions are set phrases (その時, よくなる). Whether one is meant as a whole
# depends on context, so they are left to the model pass (006) and read as their parts here.
SET_PHRASE = "exp"


class _Features(Protocol):
    pos1: str
    pos2: str
    cType: str  # noqa: N815
    cForm: str  # noqa: N815
    lemma: str | None
    lForm: str | None  # noqa: N815
    kana: str | None
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
    surface_reading: str
    part_of_speech: str
    subtype: str
    # How the word inflects (五段-カ行, 形容詞) and the form it is in here (連用形-一般).
    conjugation: str
    inflection: str
    start: int
    end: int

    @property
    def is_word(self) -> bool:
        return self.part_of_speech in WORD_PARTS_OF_SPEECH

    @property
    def is_free(self) -> bool:
        return self.subtype in FREE_SUBTYPES

    @property
    def is_number(self) -> bool:
        return self.subtype == NUMBER

    @property
    def is_potential(self) -> bool:
        """A godan verb's potential form, which UniDic files under the plain verb (読める, 読む)."""
        return (
            self.part_of_speech == VERB
            and self.conjugation.startswith(LOWER_ICHIDAN)
            and self.written_reading != self.reading
        )


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

    def tokens(self, text: str) -> list[Token]:
        tokens: list[Token] = []
        position = 0
        for node in self._tagger(text):
            start = position + len(node.white_space)
            position = start + len(node.surface)
            f = node.feature
            # UniDic lemmas may carry a disambiguating suffix, as in 私-代名詞 or コーヒー-coffee.
            lemma = (f.lemma or node.surface).split("-")[0]
            tokens.append(
                Token(
                    surface=node.surface,
                    lemma=lemma,
                    base=f.orthBase or node.surface,
                    reading=hiragana(f.lForm or node.surface),
                    written_reading=hiragana(f.kanaBase or node.surface),
                    surface_reading=hiragana(f.kana or node.surface),
                    part_of_speech=f.pos1,
                    subtype=f.pos2,
                    conjugation=f.cType,
                    inflection=f.cForm,
                    start=start,
                    end=position,
                )
            )
        return tokens


def _joined(tokens: Sequence[Token]) -> Token:
    """Tokens read as one word, whose dictionary form ends in the last token's."""
    *head, last = tokens
    spelling = "".join(t.surface for t in head) + last.base
    reading = "".join(t.surface_reading for t in head) + last.written_reading
    return Token(
        surface="".join(t.surface for t in tokens),
        lemma=spelling,
        base=spelling,
        reading=reading,
        written_reading=reading,
        surface_reading="".join(t.surface_reading for t in tokens),
        part_of_speech=last.part_of_speech,
        subtype=last.subtype,
        conjugation=last.conjugation,
        inflection=last.inflection,
        start=tokens[0].start,
        end=last.end,
    )


def _joins(tokens: Sequence[Token], index: int, start: int) -> bool:
    """Whether the token at index can extend a compound beginning at start."""
    token = tokens[index]
    previous = tokens[index - 1] if index > 0 else None
    # A counter stays with its number: 007 teaches counters as a system, while joining would
    # make 六時 and 七時 separate words and turn 一日中 into 一 + 日中 (daytime).
    after_number = previous is not None and previous.is_number
    touching = index == start or (previous is not None and previous.end == token.start)
    return token.is_word and not after_number and touching


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

    def words(self, tokens: Sequence[Token]) -> Iterator[tuple[Token, Entry | None]]:
        """Each word with its entry. A run of tokens that JMdict lists as one word, such as お茶
        or 日本語, becomes one token; the longest such run wins."""
        start = 0
        while start < len(tokens):
            compound = self._compound(tokens, start)
            if compound is not None:
                end, entry = compound
                yield _joined(tokens[start:end]), entry
                start = end
                continue

            token = tokens[start]
            if token.is_word and not token.is_free:
                yield token, self.entry(token)
            start += 1

    def _compound(self, tokens: Sequence[Token], start: int) -> tuple[int, Entry] | None:
        end = start
        while end < len(tokens) and _joins(tokens, end, start):
            end += 1

        for stop in range(end, start + 1, -1):
            entry = self._listed(_joined(tokens[start:stop]))
            if entry is not None:
                return stop, entry
        return None

    def _listed(self, compound: Token) -> Entry | None:
        form = hiragana(compound.base) if is_kana(compound.base) else compound.base
        entries = [e for e in self._by_form.get(form, ()) if SET_PHRASE not in e.parts_of_speech]
        # Sounds change where words join (日曜日 is にちようび, not にちようひ), so the reading only
        # chooses between entries that share the spelling.
        return min(
            entries,
            key=lambda e: (compound.reading not in map(hiragana, e.readings), not e.common, e.id),
            default=None,
        )

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

    def link(self, token: Token, entry: Entry | None) -> Link:
        phonetic = is_kana(token.surface)
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
