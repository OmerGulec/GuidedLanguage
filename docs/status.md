# Status

Where things stand, for whoever picks up the work next. Decisions are in `docs/decisions/`; this file is the rest.

## Built

- **Pack build** (`server/pipeline/`): Tatoeba sentences and JMdict, analysed with fugashi and unidic-lite, words linked to JMdict entries. Fails if `content/ja/link-checks.tsv` does not hold.
- **Core** (`server/core/`): events, memory via FSRS (`fsrs` 6.3.2), state derived from events, card values, unknowns per passage, ranking and candidates, the daily plan.
- **Simulator** (`server/sim/`): seeded learners against the real plan; named learners day zero, importer, three months, heavy user.
- **Word-list importer** (`server/integrations/wordlist.py`).
- Not yet: grammar, API, user database, web app.

## Running

From `server/`:

- `uv run python -m pipeline.build` downloads JMdict and Tatoeba into `data/` (gitignored) and writes `data/packs/ja/pack.sqlite`, about 75 s. The environment must allow `downloads.tatoeba.org` and `www.edrdg.org`.
- `uv run python -m pipeline.sample` rewrites `tests/fixtures/pack.sqlite` from the built pack.
- `uv run python -m pipeline.coverage`: coverage by number of words known.
- `uv run python -m sim.report`: six months of simulated workload, about 4 min.
- `uv run python -m integrations.wordlist FILE`: imports `word/reading` or `word<TAB>reading` lines, prints coverage and the next words to learn.

## Findings

- Tatoeba, words only: the 1,000 most frequent words fully cover 31% of sentences and leave one unknown in another 35%; 5,000 words give 68% and 23%. Ranking by text unlocked barely beats frequency, so the queue ranks by frequency (009).
- Simulated workload: 10 new words a day settles at about 100 reviews a day, 8% failed. A Listener at 15 words a day reaches about 260 and overruns the 200 cap.
- The owner's Renshuu export, 1,437 words: 1,410 matched, 27 guessed, 0 missing; 21.2% of passages fully known, 34.6% with one unknown. The words still missing are mostly grammar the analyser links as words (様 for よう, 下さる for ください, 仕舞う for てしまう, 就く for について) and counters (箇 in 一つ, 度 in 一度). The export is not in the repo; ask the owner to upload it again.
- Linking rules found the hard way: lemma before written forms (いる not 射る), a readings table (私 read わたし), kana words by written reading first (いい → JMdict いい), potential verbs fall back to the verb (会えた → 会う). A run of words JMdict lists as one word is one word (お茶, 日本語, 泣き出す), longest first, matched by spelling because sounds change where words join (日曜日); except set phrases (JMdict `exp`, left to the model pass) and counters, which stay with their number.

## Next

1. Design. Direction under review: a program built from the materials of a printed technical manual (the owner's references: 1970s US Navy training manuals, an oscilloscope front panel, *A Dictionary of Basic Japanese Grammar*). Materials: a Century Schoolbook-style serif (TeX Gyre Schola), Mincho for Japanese, draughting lettering for labels (osifont), heavy and hairline rules, hatching as the notation with a key on screen, dimension lines for grammar spans. Structure is software, not a page: the object being worked on in the main pane and largest on screen, its details in a side pane, readouts in fixed places, a status bar, one primary action per screen as a black key with a white inset line and its shortcut inside; secondary actions as lettered links. Lessons alone keep the page form, with key-sentence tables after the grammar dictionary. Text only for news; anything seen twice belongs in a fixed place, never in a sentence or a tutorial line. When text is needed it reads like a legal notice: plain and complete, no commands or encouragement. Black ink; one spot colour only for unknown words and ○/× marks. Rejected: dashboard looks (big-number tiles, modern grotesques), manual cosplay (figure and table captions on everything, prose for data), paper textures. Mockups on the owner's private canvas https://claude.ai/artifact/7R6Yo7NbUwATNX2XHguPyE (row D current). Next: the owner's verdict, phone versions, then tokens and primitives.
2. Full-history importers: the owner's words live in Renshuu (API), Anki review logs later.
3. Grammar (006 to 010): items, lessons, the model pass over the library. The model pass costs money and needs the owner's go-ahead.
4. API, user database, web app (011).

## Open

- Source cap (009): undefined until a second source arrives. As a count it would flatten the top of the ranking, so probably a share.
- Golden outputs per named learner (012) wait until plan behaviour settles; invariants are tested meanwhile.
- Display policy is not enforced yet; Tatoeba allows full display.
- A word marked known counts in every kanji spelling until reviewed.
- A compound JMdict lists counts as one unknown word even when its parts are known (経済活動). Rare compounds are where this bites; reading them through their parts needs a way to tell transparent compounds from opaque ones (自転車).

## Working agreements

- The owner decides what a learner can judge: clarity, workload, how a sample feels. Expertise calls are made with reasons recorded and tested on the owner later. Small reversible choices are made without asking.
- Big decisions get a second opinion from a fresh agent before they are recorded.
- Tests are checked by planting bugs one at a time, with `PYTHONDONTWRITEBYTECODE=1`; a test that misses a plausible bug is fixed.
- The owner knows about 1,400 words with weak grammar, and their first language, Turkish, shares Japanese sentence structure. They code mostly in C++ and want succinct code and plain explanations.
