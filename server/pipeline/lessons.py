"""Lesson headers: the authored grammar graph (009, 010).

Each item is a Markdown file named by its id, opening with a TOML header between `+++` lines.
Form pages are files too, but not items: they hold the idea their uses share.
"""

import re
import sys
import tomllib
from collections import Counter
from dataclasses import dataclass
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from langs.ja.content import rows
from store.paths import CONTENT

GRAMMAR = CONTENT / "grammar"
SEED_ORDER = "seed-order.txt"
NOTES = ".notes.md"
FENCE = "+++\n"
# Lowercase words joined by hyphens; a use adds its own name to its form's after a dot.
ID = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*(\.[a-z0-9]+(-[a-z0-9]+)*)?")

type Kind = Literal["form", "use", "formation", "system"]


class Header(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    kind: Kind
    name: str
    written: str | None = None
    label: str | None = None
    form: str | None = None
    key: str | None = None
    parts: list[str] = []
    after: list[str] = []
    chunk: bool = False
    nuance: bool = False
    replaces: list[str] = []


@dataclass(frozen=True, slots=True)
class Lesson:
    id: str
    header: Header
    body: str

    @property
    def prerequisites(self) -> list[str]:
        """A pattern comes after its parts unless it is met as a chunk."""
        parts = [] if self.header.chunk else self.header.parts
        return [*self.header.after, *parts]


def read_lessons(folder: Path) -> dict[str, Lesson]:
    lessons: dict[str, Lesson] = {}
    for path in sorted(folder.glob("*.md")):
        if path.name.endswith(NOTES):
            continue
        text = path.read_text()
        if not text.startswith(FENCE) or text.count(FENCE) < 2:
            raise ValueError(f"{path.name}: no header between {FENCE.strip()} lines")
        _, header, body = text.split(FENCE, 2)
        lesson_id = path.name.removesuffix(".md")
        lessons[lesson_id] = Lesson(
            lesson_id, Header.model_validate(tomllib.loads(header)), body.strip()
        )
    return lessons


def read_seed_order(folder: Path) -> list[str]:
    return [row[0] for row in rows(folder / SEED_ORDER)]


def check(lessons: dict[str, Lesson], seed_order: list[str]) -> list[str]:
    """Problems with the graph; empty when it holds."""
    items = {i: lesson for i, lesson in lessons.items() if lesson.header.kind != "form"}
    graph = {i: [p for p in lesson.prerequisites if p in items] for i, lesson in items.items()}
    problems = [p for lesson in lessons.values() for p in _header_problems(lesson, lessons)]
    try:
        TopologicalSorter(graph).prepare()
    except CycleError as error:
        problems.append(f"prerequisites form a cycle: {' → '.join(error.args[1])}")
    return problems + _seed_order_problems(graph, seed_order)


def _header_problems(lesson: Lesson, lessons: dict[str, Lesson]) -> list[str]:
    header = lesson.header
    form = lessons.get(header.form or "")
    problems: list[str] = []
    if not ID.fullmatch(lesson.id):
        problems.append("not a valid id")
    if header.kind == "form" and all(other.header.form != lesson.id for other in lessons.values()):
        problems.append("a form with no uses")
    if header.kind == "form" and header.written is None:
        problems.append("a form needs `written`")
    if header.kind == "use" and header.key is None:
        problems.append("a use needs `key`")
    if header.kind == "use" and header.form is None and header.written is None:
        problems.append("a use without a form needs `written`")
    if header.form is not None and (form is None or form.header.kind != "form"):
        problems.append(f"form {header.form} not found")
    if header.form is not None and not lesson.id.startswith(f"{header.form}."):
        problems.append("a use's id starts with its form's")
    for prerequisite in lesson.prerequisites:
        found = lessons.get(prerequisite)
        if found is None or found.header.kind == "form":
            problems.append(f"{prerequisite} not found")
    problems += [f"replaced {i} still exists" for i in header.replaces if i in lessons]
    return [f"{lesson.id}: {problem}" for problem in problems]


def _seed_order_problems(graph: dict[str, list[str]], seed_order: list[str]) -> list[str]:
    counts = Counter(seed_order)
    problems = [f"{i} listed {n} times" for i, n in counts.items() if n > 1]
    problems += [f"{i} not found" for i in counts if i not in graph]
    problems += [f"{i} missing" for i in graph if i not in counts]
    place = {i: n for n, i in enumerate(seed_order)}
    for item, prerequisites in graph.items():
        for prerequisite in prerequisites:
            if item in place and prerequisite in place and place[prerequisite] > place[item]:
                problems.append(f"{item} before its prerequisite {prerequisite}")
    return [f"seed order: {problem}" for problem in problems]


def report(folder: Path) -> None:
    lessons = read_lessons(folder)
    problems = check(lessons, read_seed_order(folder))
    for problem in problems:
        print(problem)
    kinds = Counter(lesson.header.kind for lesson in lessons.values())
    print(", ".join(f"{n} {kind}s" for kind, n in kinds.most_common()))
    written = sum(bool(lesson.body) for lesson in lessons.values())
    print(f"{written} written, {len(lessons) - written} headers only")
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    match sys.argv[1:]:
        case []:
            report(GRAMMAR)
        case _:
            sys.exit("usage: python -m pipeline.lessons")
