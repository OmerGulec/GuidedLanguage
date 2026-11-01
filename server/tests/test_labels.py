from pathlib import Path

import pytest

from pipeline.labels import read_agreed, settled
from pipeline.splits import Labels

PLACES = {"s": [3, 7, 9, 12]}
FIRST: Labels = {
    "s": [
        {"wa.topic": 0.95, "wa.contrast": 0.05},
        {"ni.target": 1.0, "ni.goal": 0.0},
        {"te.and": 0.9, "te.cause": 0.1},
        {"o.object": 1.0, "o.motion": 0.0},
    ]
}
SECOND: Labels = {
    "s": [
        {"wa.topic": 0.9, "wa.contrast": 0.1},
        {"ni.target": 0.0, "ni.goal": 1.0},
        {"te.and": 0.6, "te.cause": 0.4},
        None,
    ]
}


def test_a_label_stands_only_where_both_models_are_sure_of_the_same_use() -> None:
    assert settled(PLACES, FIRST, SECOND) == {("s", 3): "wa.topic"}
    assert settled(PLACES, SECOND, FIRST) == {("s", 3): "wa.topic"}


def test_a_set_waiting_for_labels_is_left_out_and_a_half_labelled_one_refused(
    tmp_path: Path,
) -> None:
    (tmp_path / "waiting.jsonl").write_text('{"id": "s", "forms": [{"n": 0, "at": 3}]}\n')
    assert read_agreed(tmp_path) == {}

    (tmp_path / "waiting.first.jsonl").write_text("")
    with pytest.raises(ValueError):
        read_agreed(tmp_path)
