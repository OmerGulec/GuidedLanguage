import pytest

from langs.ja.analyser import Analyser
from langs.ja.grammar import Found, Grammar, parse_rule
from pipeline.grammar import check


@pytest.fixture(scope="module")
def analyser() -> Analyser:
    return Analyser()


def found(analyser: Analyser, sentence: str, *rules: tuple[str, str]) -> dict[str, Found]:
    grammar = Grammar([parse_rule(pattern, uses) for pattern, uses in rules])
    return {sentence[f.start : f.end]: f for f in grammar.find(analyser.tokens(sentence))}


def test_the_rules_name_only_uses_and_their_checks_hold() -> None:
    assert check() == []


def test_the_longest_rule_takes_its_tokens(analyser: Analyser) -> None:
    te, teiru = ("て:接続助詞", "te.and"), ("て:接続助詞 いる:動詞", "teiru.ongoing")
    forms = found(analyser, "本を読んでいる。", te, teiru)
    assert {text: f.uses for text, f in forms.items()} == {"でいる": ("teiru.ongoing",)}


def test_a_condition_leaves_its_token_to_other_rules(analyser: Analyser) -> None:
    potential, koto = ("[*:可能]", "potential"), ("(*:動詞:連体形) こと:名詞", "koto")
    forms = found(analyser, "読めることは大切だ。", koto, potential)
    assert forms["読める"].uses == ("potential",)
    assert forms["こと"].uses == ("koto",)


def test_bracketed_tokens_belong_to_the_form_and_stay_words(analyser: Analyser) -> None:
    form = found(
        analyser, "お待ちになる。", ("お:接頭辞 [*:動詞:連用形] に:格助詞 なる:動詞", "o-ni-naru")
    )
    tokens = analyser.tokens("お待ちになる。")
    assert [tokens[i].surface for i in form["お待ちになる"].tokens] == ["お", "待ち", "に", "なる"]
    assert [tokens[i].surface for i in form["お待ちになる"].words] == ["待ち"]


def test_a_rule_without_uses_keeps_shorter_rules_off_and_specific_rules_win_ties(
    analyser: Analyser,
) -> None:
    da, attributive = ("だ:助動詞", "da"), ("だ:助動詞:連体形", "")
    forms = found(analyser, "静かな部屋だ。", da, attributive)
    assert forms["な"].uses == ()
    assert forms["だ"].uses == ("da",)


def test_a_lemma_alone_tells_apart_words_that_read_the_same(analyser: Analyser) -> None:
    about = ("に:格助詞 =つく:動詞 て:接続助詞", "ni-tsuite")
    assert "について" in found(analyser, "日本について話す。", about)
    assert found(analyser, "駅に着いて電話した。", about) == {}


def test_a_rule_must_take_a_token() -> None:
    with pytest.raises(ValueError, match="no test is part of the form"):
        parse_rule("(*:動詞) (こと:名詞)", "koto")
