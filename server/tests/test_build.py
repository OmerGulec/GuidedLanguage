from pathlib import Path

import pytest

from langs.ja.analyser import Analyser, Lexicon, read_readings
from langs.ja.dictionary import read_jmdict
from langs.ja.grammar import Grammar, read_rules
from pipeline.build import grammar_occurrences, translations, words_outside
from pipeline.grammar import RULES

FIXTURES = Path(__file__).parent / "fixtures"
READINGS = Path(__file__).parents[2] / "content" / "ja" / "readings.tsv"


@pytest.fixture(scope="module")
def analyser() -> Analyser:
    return Analyser()


@pytest.fixture(scope="module")
def lexicon() -> Lexicon:
    return Lexicon(read_jmdict(FIXTURES / "jmdict.xml"), read_readings(READINGS))


@pytest.fixture(scope="module")
def grammar() -> Grammar:
    return Grammar(read_rules(RULES))


def words(text: str, analyser: Analyser, lexicon: Lexicon, grammar: Grammar) -> list[str]:
    tokens = analyser.tokens(text)
    forms = [form for form in grammar.find(tokens) if form.uses]
    return [token.surface for token, _ in words_outside(forms, tokens, lexicon)]


def test_words_a_form_is_made_of_are_left_to_it_and_words_it_frames_stay(
    analyser: Analyser, lexicon: Lexicon, grammar: Grammar
) -> None:
    assert words("分かることができる。", analyser, lexicon, grammar) == ["分かる"]
    assert words("分かっている。", analyser, lexicon, grammar) == ["分かっ"]
    assert words("お分かりになる。", analyser, lexicon, grammar) == ["分かり"]


def test_a_form_splits_between_its_uses_by_measured_shares_or_evenly(
    analyser: Analyser, grammar: Grammar
) -> None:
    text = "猫が好き。"
    forms = [form for form in grammar.find(analyser.tokens(text)) if form.uses]

    def found(
        weights: dict[str, float], labels: dict[tuple[str, int], str] | None = None
    ) -> list[tuple[str, str, float]]:
        occurrences = grammar_occurrences("p", text, forms, weights, labels or {})
        return [(o.item, o.spelling, o.probability) for o in occurrences]

    assert found({}) == [("ga.subject", "が", 0.5), ("ga.object", "が", 0.5)]
    assert found({"ga.subject": 0.75, "ga.object": 0.25}) == [
        ("ga.subject", "が", 0.75),
        ("ga.object", "が", 0.25),
    ]
    assert found({}, {("p", 1): "ga.object"}) == [("ga.object", "が", 1.0)]
    assert found({}, {("p", 1): "wa.topic"}) == found({})
    assert found({}, {("q", 1): "ga.object"}) == found({})


def test_each_sentence_takes_its_oldest_translation() -> None:
    links = [(1, 30), (1, 20), (2, 40), (3, 50), (4, 60)]
    english = [(20, "older"), (30, "newer"), (40, "only"), (60, "not wanted")]

    assert translations(links, english, wanted={1, 2, 3}) == {1: "older", 2: "only"}
