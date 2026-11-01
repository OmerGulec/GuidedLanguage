"""Sentences for the 006 test set, for two models to label.

`choose NAME PARTS` picks easy library passages holding the forms of the first grammar uses, in
rank order, that still lack settled passages. It writes them as `NAME.jsonl` beside a guide to
each use's key, and splits them into parts for labellers under `data/labelling/NAME/`.
`merge NAME MODEL` joins the labelled parts into `NAME.MODEL.jsonl`, which the pack build
reads (pipeline.labels).
"""

import json
import random
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict

from core.candidates import Ranking, ranked, ranking
from core.pack import Pack, Passage
from core.passages import SETTLED
from core.settings import Settings
from pipeline.labels import SAMPLES
from pipeline.lessons import GRAMMAR, read_lessons
from store.pack import UnsettledForm, read_eligible, read_pack, read_passages, read_unsettled_forms
from store.paths import DATA, PACK

# A use stays a target until this many eligible passages settle it, about what 006 asks for.
WANTED = 50
TARGET_USES = 20
PER_FORM = 60
# An easy passage: short, and every word among the most frequent.
COMMON_WORDS = 2000
LONGEST = 30
SEED = 6
PARTS = DATA / "labelling"

GUIDE = """\
# Labelling guide: {name}

Each line of a part file is a Japanese sentence with numbered forms. Each form lists the
grammar uses it may have; the uses are explained below.

Judge each sentence as a careful native reader would. For every form, give each listed use a
probability, the probabilities summing to 1. Be decisive where the sentence is clear: give the
use it has 1. Spread probability only where the sentence itself is ambiguous. Where no listed
use fits, because the form is part of a fixed word or expression or was found by mistake, set
`none_fit` to true and every probability to 0.

Write one JSON object per input line, in the same order, and nothing else:

    {{"id": "...", "forms": [{{"n": 0, "probabilities": {{"wa.topic": 1, "wa.contrast": 0}},
      "none_fit": false}}]}}

on a single line.

Every form of every sentence must appear, with every use it lists.

## Uses

{uses}
"""


def choose(name: str, parts: int) -> None:
    pack, eligible = read_pack(PACK), read_eligible(PACK)
    pack_ranking = ranking(pack, Settings(), eligible)
    texts = {p.id: p for p in read_passages(PACK)}

    targets = _targets(pack, pack_ranking, eligible)
    easy = _easy(pack, pack_ranking, eligible, texts, name)
    forms: dict[str, list[UnsettledForm]] = defaultdict(list)
    for form in read_unsettled_forms(PACK):
        if form.passage in easy:
            forms[form.passage].append(form)
    chosen = cover(forms, targets, PER_FORM)

    lines = [_line(texts[passage], forms[passage]) for passage in chosen]
    _write_lines(SAMPLES / f"{name}.jsonl", lines)
    met = sorted({use for passage in chosen for form in forms[passage] for use in form.uses})
    (SAMPLES / f"{name}.guide.md").write_text(_guide(name, met))
    folder = PARTS / name
    folder.mkdir(parents=True, exist_ok=True)
    for part in range(parts):
        _write_lines(folder / f"part-{part + 1}.jsonl", lines[part::parts])
    print(f"targets: {' '.join(targets)}")
    count = sum(len(forms[passage]) for passage in chosen)
    print(f"{len(lines)} sentences, {count} forms, in {folder}")


def _targets(pack: Pack, pack_ranking: Ranking, eligible: NDArray[np.bool_]) -> list[str]:
    """The first uses, in rank order, with fewer settled passages than wanted."""
    settled = (pack.appearance_probabilities >= SETTLED) & eligible[pack.appearance_passages]
    settled_columns: list[int] = pack.appearance_columns[settled].tolist()
    count = Counter(pack.columns[column].item for column in settled_columns)
    uses = [i for i, item in pack.grammar.items() if item.kind == "use"]
    order = sorted(uses, key=lambda use: (-pack_ranking.rank.get(use, 0.0), use))
    return [use for use in order if count[use] < WANTED][:TARGET_USES]


def _easy(
    pack: Pack,
    pack_ranking: Ranking,
    eligible: NDArray[np.bool_],
    texts: Mapping[str, Passage],
    name: str,
) -> set[str]:
    """Short, translated passages of common words that no other set has labelled."""
    # The rank of a passage's rarest word; a word the dictionary lacks makes it hard.
    frequency = {i: f for i, f in pack_ranking.frequency.items() if i not in pack.grammar}
    words = ranked(frequency, set())
    word_rank = {item: n for n, item in enumerate(words) if item.startswith("w:")}
    rarest = np.zeros(len(pack.passages), dtype=np.int64)
    column_rank = np.array(
        [word_rank.get(c.item, 0 if c.item in pack.grammar else len(words)) for c in pack.columns]
    )
    np.maximum.at(rarest, pack.appearance_passages, column_rank[pack.appearance_columns])

    others = (p for p in SAMPLES.glob("*.jsonl") if p.name.split(".")[0] != name)
    labelled = {line_id for path in others for line_id in _ids(path)}
    return {
        passage
        for i, passage in enumerate(pack.passages)
        if eligible[i]
        and rarest[i] < COMMON_WORDS
        and len(texts[passage].text) <= LONGEST
        and passage not in labelled
    }


def _line(passage: Passage, forms: Sequence[UnsettledForm]) -> dict[str, object]:
    return {
        "id": passage.id,
        "tatoeba": passage.position,
        "text": passage.text,
        "forms": [
            {"n": n, "text": passage.text[f.start : f.end], "at": f.start, "uses": f.uses}
            for n, f in enumerate(forms)
        ],
    }


class FormToLabel(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    n: int
    uses: list[str]


class ToLabel(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    id: str
    forms: list[FormToLabel]


class LabelledForm(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    n: int
    probabilities: dict[str, float]
    none_fit: bool = False


class Labelled(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    id: str
    forms: list[LabelledForm]


def merge(name: str, model: str) -> None:
    labelled: dict[str, tuple[str, Labelled]] = {}
    for path in (PARTS / name).glob(f"part-*.{model}.jsonl"):
        for line in path.read_text().splitlines():
            if line.strip():
                sentence = Labelled.model_validate_json(line)
                labelled[sentence.id] = (line, sentence)
    lines = (SAMPLES / f"{name}.jsonl").read_text().splitlines()
    sentences = [ToLabel.model_validate_json(line) for line in lines if line.strip()]

    wrong = [s.id for s in sentences if s.id not in labelled or not matches(s, labelled[s.id][1])]
    if wrong:
        raise SystemExit(f"{len(wrong)} sentences missing or mislabelled: {' '.join(wrong)}")
    merged = "".join(labelled[s.id][0] + "\n" for s in sentences)
    (SAMPLES / f"{name}.{model}.jsonl").write_text(merged)
    print(f"{len(sentences)} sentences labelled by {model}")


def matches(sentence: ToLabel, labelled: Labelled) -> bool:
    """A labelling covers every form of its sentence by number, each with exactly its uses."""
    uses = {form.n: set(form.uses) for form in sentence.forms}
    return uses == {form.n: set(form.probabilities) for form in labelled.forms}


def cover(
    forms: Mapping[str, Sequence[UnsettledForm]], targets: Sequence[str], per_form: int
) -> list[str]:
    """Up to `per_form` passages for each form a target use may be, counting passages already
    chosen for another form."""
    by_form: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for passage, found in forms.items():
        for form in found:
            by_form[form.uses].append(passage)
    chosen: dict[str, None] = {}
    shuffle = random.Random(SEED)
    for target in targets:
        for uses, passages in sorted(by_form.items()):
            if target not in uses:
                continue
            have = sum(passage in chosen for passage in passages)
            pool = sorted(set(passages) - chosen.keys())
            shuffle.shuffle(pool)
            chosen |= dict.fromkeys(pool[: max(0, per_form - have)])
    return list(chosen)


def _guide(name: str, uses: list[str]) -> str:
    lessons = read_lessons(GRAMMAR)
    entries = [f"- `{use}`, {lessons[use].header.name}: {lessons[use].header.key}" for use in uses]
    return GUIDE.format(name=name, uses="\n".join(entries))


def _ids(path: Path) -> list[str]:
    return [json.loads(line)["id"] for line in path.read_text().splitlines() if line.strip()]


def _write_lines(path: Path, lines: Sequence[Mapping[str, object]]) -> None:
    path.write_text("".join(json.dumps(line, ensure_ascii=False) + "\n" for line in lines))


if __name__ == "__main__":
    match sys.argv[1:]:
        case ["choose", name, parts]:
            choose(name, int(parts))
        case ["merge", name, model]:
            merge(name, model)
        case _:
            raise SystemExit("usage: pipeline.testset choose NAME PARTS | merge NAME MODEL")
