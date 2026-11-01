from pathlib import Path

from langs.ja.dictionary import read_jmdict

FIXTURES = Path(__file__).parent / "fixtures"


def test_every_sense_is_kept_in_order_and_the_first_is_the_main_meaning() -> None:
    drink = next(e for e in read_jmdict(FIXTURES / "jmdict.xml") if e.id == 1169870)

    assert len(drink.senses) == 7
    assert drink.senses[:2] == (
        ("to drink", "to swallow", "to take (medicine)"),
        ("to smoke (tobacco)",),
    )
    assert drink.glosses == drink.senses[0]
