import json
from pathlib import Path

import pytest

from pipeline.splits import PSEUDO_COUNT, agreement, read_labels, shares, split


def labels_file(path: Path, sentences: list[list[dict[str, float] | None]]) -> Path:
    lines: list[str] = []
    for number, forms in enumerate(sentences):
        written = [
            {"n": n, "probabilities": p or {}, "none_fit": p is None} for n, p in enumerate(forms)
        ]
        lines.append(json.dumps({"id": f"s{number}", "forms": written}))
    path.write_text("\n".join(lines) + "\n")
    return path


def test_a_share_is_the_mean_probability_where_the_use_could_be_meant(tmp_path: Path) -> None:
    sentences: list[list[dict[str, float] | None]] = [
        [{"wa.topic": 1, "wa.contrast": 0}],
        [{"wa.topic": 0.5, "wa.contrast": 0.5}, None],
    ]
    measured = shares(read_labels(labels_file(tmp_path / "l.jsonl", sentences)))
    assert measured == {
        "wa.contrast": (0.5 + PSEUDO_COUNT) / 3,
        "wa.topic": (1.5 + PSEUDO_COUNT) / 3,
    }


def test_a_form_splits_by_shares_and_evenly_among_uses_never_measured() -> None:
    assert split(("a", "b"), {"a": 0.6, "b": 0.2}) == pytest.approx({"a": 0.75, "b": 0.25})
    assert split(("a", "b"), {}) == {"a": 0.5, "b": 0.5}


def test_agreement_counts_the_same_most_likely_use_and_none_fit_alike(tmp_path: Path) -> None:
    first = read_labels(labels_file(tmp_path / "a.jsonl", [[{"x": 0.9, "y": 0.1}, None]]))
    second = read_labels(labels_file(tmp_path / "b.jsonl", [[{"x": 0.6, "y": 0.4}, {"x": 1}]]))
    assert agreement(first, second) == 0.5
