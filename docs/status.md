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

- Tatoeba, words only: the 1,000 most frequent words fully cover 33% of sentences and leave one unknown in another 33%; 5,000 words give 74% and 19%. Ranking by text unlocked barely beats frequency, so the queue ranks by frequency (009).
- Simulated workload: 10 new words a day settles at about 100 reviews a day, 8% failed. A Listener at 15 words a day reaches about 260 and overruns the 200 cap.
- The owner's Renshuu export, 1,437 words: 1,410 matched, 27 guessed, 0 missing; 20.5% of passages fully known, 31.4% with one unknown. Understated: the analyser splits compounds (お茶 → 御 + 茶, 日本語 → 日本 + 語, 子供たち → 子供 + 達) and grammar is not modelled (ください → 下さる, てしまう → 仕舞う). The export is not in the repo; ask the owner to upload it again.
- Linking rules found the hard way: lemma before written forms (いる not 射る), a readings table (私 read わたし), kana words by written reading first (いい → JMdict いい), potential verbs fall back to the verb (会えた → 会う).

## Next

1. Merge consecutive tokens into the longest JMdict entry when building the pack (お茶, 日本語), then re-run the owner's import.
2. Design: the owner sends 3 to 5 references; three deliberately different reader mockups; then tokens and primitives. Avoid default Claude visuals: purple or indigo, gradients, rounded cards with soft shadows, Inter, emoji icons, pills everywhere, progress rings and streaks.
3. Full-history importers: the owner's words live in Renshuu (API), Anki review logs later.
4. Grammar (006 to 010): items, lessons, the model pass over the library. The model pass costs money and needs the owner's go-ahead.
5. API, user database, web app (011).

## Open

- Source cap (009): undefined until a second source arrives. As a count it would flatten the top of the ranking, so probably a share.
- Golden outputs per named learner (012) wait until plan behaviour settles; invariants are tested meanwhile.
- Display policy is not enforced yet; Tatoeba allows full display.
- A word marked known counts in every kanji spelling until reviewed.

## Working agreements

- The owner decides what a learner can judge: clarity, workload, how a sample feels. Expertise calls are made with reasons recorded and tested on the owner later. Small reversible choices are made without asking.
- Big decisions get a second opinion from a fresh agent before they are recorded.
- Tests are checked by planting bugs one at a time, with `PYTHONDONTWRITEBYTECODE=1`; a test that misses a plausible bug is fixed.
- The owner knows about 1,400 words with weak grammar, and their first language, Turkish, shares Japanese sentence structure. They code mostly in C++ and want succinct code and plain explanations.
