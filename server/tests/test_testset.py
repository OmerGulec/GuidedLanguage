from pipeline.testset import FormToLabel, Labelled, LabelledForm, ToLabel, cover, matches
from store.pack import UnsettledForm

TOPIC_USES: list[str] = ["wa.contrast", "wa.topic"]
OBJECT_USES: list[str] = ["o.motion", "o.object"]
TOPIC, OBJECT = tuple(TOPIC_USES), tuple(OBJECT_USES)


def forms_in(passage: str, *uses: tuple[str, ...]) -> list[UnsettledForm]:
    return [UnsettledForm(passage, n, n + 1, u) for n, u in enumerate(uses)]


def test_each_target_form_gets_its_quota_counting_passages_chosen_for_another() -> None:
    forms = {
        **{f"both{i}": forms_in(f"both{i}", TOPIC, OBJECT) for i in range(5)},
        **{f"o{i}": forms_in(f"o{i}", OBJECT) for i in range(5)},
    }
    chosen = cover(forms, ["wa.topic", "o.object", "o.motion"], per_form=3)

    assert sorted(p[:4] for p in chosen) == ["both"] * 3
    assert cover(forms, ["ni.target"], per_form=3) == []


def test_a_labelling_must_cover_each_form_by_number_with_exactly_its_uses() -> None:
    sentence = ToLabel(
        id="s", forms=[FormToLabel(n=0, uses=TOPIC_USES), FormToLabel(n=1, uses=OBJECT_USES)]
    )

    def labelled(*forms: tuple[int, list[str]]) -> Labelled:
        given = [LabelledForm(n=n, probabilities=dict.fromkeys(uses, 0.5)) for n, uses in forms]
        return Labelled(id="s", forms=given)

    assert matches(sentence, labelled((1, OBJECT_USES), (0, TOPIC_USES)))
    assert not matches(sentence, labelled((0, TOPIC_USES)))
    assert not matches(sentence, labelled((0, TOPIC_USES), (2, OBJECT_USES)))
    assert not matches(sentence, labelled((0, TOPIC_USES), (1, ["o.object"])))
