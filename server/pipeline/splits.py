"""Each grammar use's share of the forms that may be it, measured on a labelled sample (006).

Until the model pass labels every passage, a form found in a passage splits between its uses by
these shares instead of evenly.
"""

import sys
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from langs.ja.content import rows
from pipeline.lessons import GRAMMAR

SPLITS = GRAMMAR / "splits.tsv"
# Half an observation added to every use, so one the sample rarely met keeps a modest share.
PSEUDO_COUNT = 0.5


class _Form(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    n: int
    probabilities: dict[str, float]
    none_fit: bool = False


class _Sentence(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    id: str
    forms: list[_Form]


# Per sentence, per form: the probability of each use, or None where no listed use fits.
type Labels = dict[str, list[dict[str, float] | None]]


def read_labels(path: Path) -> Labels:
    labels: Labels = {}
    for line in path.read_text().splitlines():
        if line.strip():
            sentence = _Sentence.model_validate_json(line)
            forms = sorted(sentence.forms, key=lambda f: f.n)
            labels[sentence.id] = [None if f.none_fit else f.probabilities for f in forms]
    return labels


def shares(labels: Labels) -> dict[str, float]:
    """A use's mean probability over the forms that could be it."""
    total: dict[str, float] = defaultdict(float)
    seen: dict[str, int] = defaultdict(int)
    for forms in labels.values():
        for probabilities in forms:
            for use, p in (probabilities or {}).items():
                total[use] += p
                seen[use] += 1
    return {use: (total[use] + PSEUDO_COUNT) / (seen[use] + 1) for use in sorted(seen)}


def split(uses: Iterable[str], weights: Mapping[str, float]) -> dict[str, float]:
    """A form's probability per use: by measured share, evenly for uses never measured."""
    known = [weights.get(use, PSEUDO_COUNT) for use in uses]
    return {use: w / sum(known) for use, w in zip(uses, known, strict=True)}


def agreement(first: Labels, second: Labels) -> float:
    """How often two labellings pick the same most likely use, none-fit counting as a pick."""
    same = total = 0
    for sentence, forms in first.items():
        for mine, theirs in zip(forms, second.get(sentence, []), strict=False):
            total += 1
            same += _pick(mine) == _pick(theirs)
    return same / total if total else 0.0


def _pick(probabilities: Mapping[str, float] | None) -> str | None:
    return max(probabilities, key=lambda u: probabilities[u]) if probabilities else None


def read_splits(path: Path) -> dict[str, float]:
    return {use: float(weight) for use, weight in rows(path)} if path.exists() else {}


def write_splits(weights: Mapping[str, float], path: Path, source: str) -> None:
    lines = [f"# Measured shares of each use (pipeline.splits), from {source}.", "# use\tshare"]
    lines += [f"{use}\t{weight:.4f}" for use, weight in weights.items()]
    path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    match sys.argv[1:]:
        case [primary, *others]:
            labels = read_labels(Path(primary))
            write_splits(shares(labels), SPLITS, Path(primary).name)
            print(f"{sum(map(len, labels.values()))} forms in {len(labels)} sentences")
            for other in others:
                print(f"agreement with {other}: {agreement(labels, read_labels(Path(other))):.1%}")
        case _:
            sys.exit("usage: python -m pipeline.splits LABELS [SECOND_LABELS...]")
