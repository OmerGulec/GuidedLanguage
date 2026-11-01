"""Grammar forms found by authored rules over the analyser's tokens (006).

A rule is a run of token tests and the uses its form may have. Where a form has one use the
rule settles it; where it has several, the model pass chooses among them. A rule with no uses
marks tokens that are not grammar items, so that shorter rules leave them alone (the な of
静かな).

A test is a lemma or its reading (alternatives joined by |; =lemma for the lemma alone) or *
for any token, then :tags that must each name the token's part of speech, subtype, or a prefix
of its conjugation or inflection. 可能 names a godan verb's potential form. Written plainly, a
test is part of the form and its token is not read as a word as well; in brackets it is part
of the form and still a word (the verb in お待ちになる); in parentheses it is only a condition,
and other rules may use its token (the verb before こと).

Rules apply longest first, by the tokens they take, then by their number of tests, then by
how many values and tags they name, so that 静かな's な finds だ:助動詞:連体形 before
だ:助動詞; then in the order written.
"""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from langs.ja.analyser import Analyser, Token
from langs.ja.content import rows

ANY = "*"
POTENTIAL = "可能"
NONE = "-"

type Role = Literal["form", "word", "condition"]


@dataclass(frozen=True, slots=True)
class Test:
    # None matches any token.
    values: frozenset[str] | None
    lemma_only: bool
    tags: tuple[str, ...]
    role: Role

    def matches(self, token: Token) -> bool:
        if self.values is not None:
            names = {token.lemma} if self.lemma_only else {token.lemma, token.reading}
            if not self.values & names:
                return False
        return all(_tagged(token, tag) for tag in self.tags)


def _tagged(token: Token, tag: str) -> bool:
    if tag == POTENTIAL:
        return token.is_potential
    return (
        tag in (token.part_of_speech, token.subtype)
        or token.conjugation.startswith(tag)
        or token.inflection.startswith(tag)
    )


@dataclass(frozen=True, slots=True)
class Rule:
    tests: tuple[Test, ...]
    uses: tuple[str, ...]

    @property
    def taken(self) -> int:
        return sum(test.role != "condition" for test in self.tests)

    @property
    def named(self) -> int:
        return sum(len(test.tags) + (test.values is not None) for test in self.tests)


@dataclass(frozen=True, slots=True)
class Found:
    uses: tuple[str, ...]
    # The tokens the form is made of, and those of them that are still read as words.
    tokens: tuple[int, ...]
    words: tuple[int, ...]
    start: int
    end: int


def parse_rule(pattern: str, uses: str) -> Rule:
    rule = Rule(tuple(map(_test, pattern.split())), tuple(uses.split()))
    if rule.taken == 0:
        raise ValueError(f"{pattern}: no test is part of the form")
    return rule


def _test(text: str) -> Test:
    role: Role = "form"
    if text.startswith("[") and text.endswith("]"):
        role, text = "word", text[1:-1]
    elif text.startswith("(") and text.endswith(")"):
        role, text = "condition", text[1:-1]
    value, *tags = text.split(":")
    values = None if value == ANY else frozenset(value.removeprefix("=").split("|"))
    return Test(values, value.startswith("="), tuple(tags), role)


def read_rules(path: Path) -> list[Rule]:
    return [parse_rule(row[0], row[1] if len(row) > 1 else "") for row in rows(path)]


class Grammar:
    def __init__(self, rules: Sequence[Rule]) -> None:
        self._rules = rules
        # Each rule is looked up by its first test that names a value.
        self._by_value: dict[str, list[tuple[int, int]]] = defaultdict(list)
        self._unnamed: list[tuple[int, int]] = []
        for number, rule in enumerate(rules):
            named = [(i, t.values) for i, t in enumerate(rule.tests) if t.values is not None]
            if not named:
                self._unnamed.append((number, 0))
                continue
            anchor, values = named[0]
            for value in values:
                self._by_value[value].append((number, anchor))

    def find(self, tokens: Sequence[Token]) -> list[Found]:
        matches: set[tuple[int, int]] = set()
        for index, token in enumerate(tokens):
            near = {*self._by_value[token.lemma], *self._by_value[token.reading], *self._unnamed}
            for number, anchor in near:
                start = index - anchor
                if self._matches(self._rules[number], tokens, start):
                    matches.add((number, start))

        def precedence(match: tuple[int, int]) -> tuple[int, int, int, int, int]:
            rule = self._rules[match[0]]
            return (-rule.taken, -len(rule.tests), -rule.named, match[0], match[1])

        taken: set[int] = set()
        found: list[Found] = []
        for number, start in sorted(matches, key=precedence):
            rule = self._rules[number]
            parts = [(start + i, t.role) for i, t in enumerate(rule.tests) if t.role != "condition"]
            indexes = tuple(i for i, _ in parts)
            if taken.intersection(indexes):
                continue
            taken.update(indexes)
            words = tuple(i for i, role in parts if role == "word")
            span = (tokens[indexes[0]].start, tokens[indexes[-1]].end)
            found.append(Found(rule.uses, indexes, words, *span))
        return sorted(found, key=lambda f: f.start)

    @staticmethod
    def _matches(rule: Rule, tokens: Sequence[Token], start: int) -> bool:
        if start < 0 or start + len(rule.tests) > len(tokens):
            return False
        return all(test.matches(tokens[start + i]) for i, test in enumerate(rule.tests))


def check_grammar(analyser: Analyser, grammar: Grammar, path: Path) -> list[str]:
    """Sentences whose grammar must be found as written: a form's text and its uses, or - for
    none. Returns a line for each that is not."""
    failures: list[str] = []
    for sentence, text, uses in rows(path):
        found = {sentence[f.start : f.end]: f.uses for f in grammar.find(analyser.tokens(sentence))}
        expected: set[str] = set() if uses == NONE else set(uses.split())
        actual = set(found.get(text, ()))
        if actual != expected:
            failures.append(
                f"{sentence} {text}: found {' '.join(sorted(actual)) or NONE}, expected {uses}"
            )
    return failures
