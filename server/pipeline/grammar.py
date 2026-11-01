"""How much of the library's grammar the rules find (006), and whether they still hold."""

import sys
from collections import Counter

from langs.ja.analyser import Analyser
from langs.ja.grammar import Grammar, check_grammar, read_rules
from pipeline.lessons import GRAMMAR, read_lessons
from store.pack import read_passages
from store.paths import PACK

RULES = GRAMMAR / "rules.tsv"
CHECKS = GRAMMAR / "checks.tsv"
# Particles and endings are grammar; when no rule takes one, a rule is missing.
MARKERS = ("助詞", "助動詞")
SHOWN = 30


def check() -> list[str]:
    """Rules that name no use, and checks that fail."""
    uses = {i for i, lesson in read_lessons(GRAMMAR).items() if lesson.header.kind == "use"}
    rules = read_rules(RULES)
    named = {use for rule in rules for use in rule.uses}
    problems = [f"rules name {use}, which is not a use" for use in sorted(named - uses)]
    return problems + check_grammar(Analyser(), Grammar(rules), CHECKS)


def report() -> None:
    problems = check()
    for problem in problems:
        print(problem)

    uses = {i for i, lesson in read_lessons(GRAMMAR).items() if lesson.header.kind == "use"}
    analyser, grammar = Analyser(), Grammar(read_rules(RULES))
    passages = read_passages(PACK)
    forms: Counter[tuple[str, ...]] = Counter()
    missed: Counter[str] = Counter()
    found_uses: set[str] = set()
    finds = choices = 0
    for passage in passages:
        tokens = analyser.tokens(passage.text)
        everything = grammar.find(tokens)
        found = [f for f in everything if f.uses]
        taken = {i for f in everything for i in f.tokens}
        finds += len(found)
        choices += sum(len(f.uses) > 1 for f in found)
        forms.update({f.uses for f in found})
        found_uses.update(use for f in found for use in f.uses)
        missed.update(
            f"{t.lemma} {t.part_of_speech}/{t.subtype}"
            for i, t in enumerate(tokens)
            if i not in taken and t.part_of_speech in MARKERS
        )

    print(f"{len(passages)} passages, {finds} grammar forms found")
    print(
        f"settled by rules: {1 - choices / finds:.1%}; left to the model to choose a use: "
        f"{choices / finds:.1%}"
    )
    print(f"uses no rule finds: {', '.join(sorted(uses - found_uses))}")
    print("most common forms, by passages:")
    for form, count in forms.most_common(SHOWN):
        print(f"  {count / len(passages):6.2%}  {' '.join(form)}")
    print("markers no rule takes:")
    for marker, count in missed.most_common(SHOWN):
        print(f"  {count:7}  {marker}")
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    match sys.argv[1:]:
        case []:
            report()
        case _:
            sys.exit("usage: python -m pipeline.grammar")
