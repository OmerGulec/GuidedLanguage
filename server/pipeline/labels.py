"""Labels that settle a form's use in one passage (006).

Each labelled set is a file of sentences with the forms to label, `NAME.jsonl`, and the two
labellings of it by different models, `NAME.<model>.jsonl`. Where both pick the same use and
both are sure of it, the label stands; anywhere else the form keeps its shares. A set not yet
labelled is left out.
"""

from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from pipeline.lessons import GRAMMAR
from pipeline.splits import Labels, read_labels

SAMPLES = GRAMMAR / "samples"
LABELLINGS_PER_SET = 2
# A labelling is sure of a use at this probability; a label stands when both are sure of one.
SURE = 0.9

# A form's position in its passage: the passage id and the form's first character.
type Place = tuple[str, int]


class _Form(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    n: int
    at: int


class _Sentence(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    id: str
    forms: list[_Form]


def read_agreed(folder: Path) -> dict[Place, str]:
    agreed: dict[Place, str] = {}
    for sentences in sorted(p for p in folder.glob("*.jsonl") if p.stem.count(".") == 0):
        labellings = sorted(folder.glob(f"{sentences.stem}.*.jsonl"))
        if not labellings:
            continue
        if len(labellings) != LABELLINGS_PER_SET:
            raise ValueError(f"{sentences.name}: {len(labellings)} labellings, not two")
        places = _places(sentences)
        first, second = (read_labels(path) for path in labellings)
        agreed |= settled(places, first, second)
    return agreed


def settled(places: Mapping[str, list[int]], first: Labels, second: Labels) -> dict[Place, str]:
    """Forms whose use both labellings are sure of."""
    agreed: dict[Place, str] = {}
    for passage, starts in places.items():
        pairs = zip(first.get(passage, []), second.get(passage, []), strict=False)
        for at, (mine, theirs) in zip(starts, pairs, strict=False):
            if mine is None or theirs is None:
                continue
            use, chance = max(mine.items(), key=lambda pair: pair[1])
            if chance >= SURE and theirs.get(use, 0.0) >= SURE:
                agreed[passage, at] = use
    return agreed


def _places(path: Path) -> dict[str, list[int]]:
    """Each sentence's form starts, in the order of their numbers, as the labellings list them."""
    places: dict[str, list[int]] = {}
    for line in path.read_text().splitlines():
        if line.strip():
            sentence = _Sentence.model_validate_json(line)
            places[sentence.id] = [f.at for f in sorted(sentence.forms, key=lambda f: f.n)]
    return places
