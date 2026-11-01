from api.library import load_library, passage_view
from core.events import Marked
from core.state import derive
from core.values import values
from store.pack import read_unsettled_forms
from tests.history import TOKYO, at, event
from tests.packs import FIXTURE

LIBRARY = load_library(FIXTURE, TOKYO)


def test_an_unsettled_form_lists_the_uses_taught_never_one_marked_ignored() -> None:
    form = next(f for f in read_unsettled_forms(FIXTURE) if len(f.uses) >= 2)
    known, ignored = form.uses[:2]
    state = derive(
        [
            event(at(1, 8), Marked(known, "known", "hand")),
            event(at(1, 8), Marked(ignored, "ignored", "hand")),
        ],
        TOKYO,
    )
    reading = values(state, LIBRARY.pack, TOKYO, at(2, 4), "reading")

    view = passage_view(LIBRARY, form.passage, state, reading)
    assert view is not None
    span = next(span for span in view.spans if span.start == form.start)
    assert span.items == [known]
    assert set(view.items) >= {known}
