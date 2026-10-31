import json
from pathlib import Path

from pipeline.lessons import GRAMMAR, SEED_ORDER, check, read_lessons, read_seed_order

type Value = str | bool | list[str]


def write(folder: Path, lesson_id: str, **header: Value) -> None:
    # JSON strings and arrays are valid TOML.
    lines = [
        f"{k} = {str(v).lower() if isinstance(v, bool) else json.dumps(v)}"
        for k, v in header.items()
    ]
    (folder / f"{lesson_id}.md").write_text("+++\n" + "\n".join(lines) + "\n+++\n")


def problems(folder: Path, seed_order: list[str]) -> list[str]:
    (folder / SEED_ORDER).write_text("\n".join(seed_order) + "\n")
    return check(read_lessons(folder), read_seed_order(folder))


def te_iru(folder: Path) -> None:
    write(folder, "te-ta", kind="formation", name="te-form")
    write(folder, "teiru", kind="form", name="te-iru", written="ている")
    write(
        folder, "teiru.ongoing", kind="use", name="ongoing", form="teiru", key="k", after=["te-ta"]
    )


def test_the_grammar_content_holds() -> None:
    assert check(read_lessons(GRAMMAR), read_seed_order(GRAMMAR)) == []


def test_a_small_graph_holds(tmp_path: Path) -> None:
    te_iru(tmp_path)
    assert problems(tmp_path, ["te-ta", "teiru.ongoing"]) == []


def test_references_to_missing_items_and_to_form_pages_are_reported(tmp_path: Path) -> None:
    te_iru(tmp_path)
    write(tmp_path, "temo", kind="use", name="even if", written="ても", key="k", parts=["te"])
    write(tmp_path, "temoii", kind="use", name="may", written="てもいい", key="k", after=["teiru"])
    found = problems(tmp_path, ["te-ta", "teiru.ongoing", "temo", "temoii"])
    assert found == ["temo: te not found", "temoii: teiru not found"]


def test_a_cycle_is_reported(tmp_path: Path) -> None:
    write(tmp_path, "a", kind="use", name="a", written="a", key="k", after=["b"])
    write(tmp_path, "b", kind="use", name="b", written="b", key="k", parts=["a"])
    assert any("cycle" in p for p in problems(tmp_path, ["a", "b"]))


def test_the_seed_order_puts_prerequisites_first_but_a_chunk_may_precede_its_parts(
    tmp_path: Path,
) -> None:
    te_iru(tmp_path)
    write(tmp_path, "temo", kind="use", name="even if", written="ても", key="k", after=["te-ta"])
    write(tmp_path, "temoii", kind="use", name="may", written="てもいい", key="k", parts=["temo"])
    order = ["te-ta", "teiru.ongoing", "temoii", "temo"]
    assert problems(tmp_path, order) == ["seed order: temoii before its prerequisite temo"]
    write(
        tmp_path,
        "temoii",
        kind="use",
        name="may",
        written="てもいい",
        key="k",
        parts=["temo"],
        chunk=True,
    )
    assert problems(tmp_path, order) == []


def test_the_seed_order_lists_every_item_once_and_no_form_pages(tmp_path: Path) -> None:
    te_iru(tmp_path)
    found = problems(tmp_path, ["te-ta", "te-ta", "teiru"])
    assert found == [
        "seed order: te-ta listed 2 times",
        "seed order: teiru not found",
        "seed order: teiru.ongoing missing",
    ]


def test_headers_missing_what_their_kind_needs_are_reported(tmp_path: Path) -> None:
    write(tmp_path, "teiru", kind="form", name="te-iru")
    write(tmp_path, "te-oku", kind="form", name="te-oku", written="ておく")
    write(tmp_path, "teiru.ongoing", kind="use", name="ongoing", form="teiru")
    write(tmp_path, "state", kind="use", name="state", form="teiru", key="k", replaces=["te-oku"])
    found = problems(tmp_path, ["teiru.ongoing", "state"])
    assert found == [
        "state: a use's id starts with its form's",
        "state: replaced te-oku still exists",
        "te-oku: a form with no uses",
        "teiru: a form needs `written`",
        "teiru.ongoing: a use needs `key`",
    ]
