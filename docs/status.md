# Status

Where things stand, for whoever picks up the work next. Decisions are in `docs/decisions/`; this file is the rest.

## Built

- **Pack build** (`server/pipeline/`): Tatoeba sentences and JMdict, analysed with fugashi and unidic-lite, words linked to JMdict entries, grammar found by the rules. A form's uses share its occurrence evenly until the model pass measures them; a word a form is made of (こと, できる in ことができる) is left to the form. Fails if `content/ja/link-checks.tsv` or the grammar checks do not hold.
- **Core** (`server/core/`): events, memory via FSRS (`fsrs` 6.3.2), state derived from events, card values, unknowns per passage, ranking and candidates, the daily plan. Grammar counts in unknowns (first grammar change, approved by the owner): each appearance carries the probability that its item is meant, a grammar use takes its `sentence` card's value by eye and by ear, nuance items always count as known, and grammar stays out of the word ranking. Grammar is not yet planned: no grammar candidates, prerequisites, cap or explanation steps.
- **Simulator** (`server/sim/`): seeded learners against the real plan; named learners day zero, importer, three months, heavy user.
- **Word-list importer** (`server/integrations/wordlist.py`).
- **Renshuu importer** (`server/integrations/renshuu.py`): fetches the learner's full answer history through Renshuu's API and replays it as Introduced and Reviewed events (013). Per card and day one review, failed if any answer that day was wrong. Kanji > Kana and Kanji > Meaning feed recognize in the kanji spelling; Kana > Meaning recognize in kana; Listening listen; Accent pitch; Meaning > Kana and Meaning > Kanji cloze; Kana > Kanji and Writing nothing. Reviews of rungs outside the goal are kept and not scheduled.
- **Grammar graph** (`content/ja/grammar/`, checked by `server/pipeline/lessons.py`): one Markdown file per item named by its id, with a TOML header (010): 199 items for about JLPT N5 to N4 plus what 009 adds (179 uses, 11 formations, 9 systems) and 37 form pages, revised after a second opinion. `seed-order.txt` is the hand order (009). Headers only, except the sample lesson for ている (form page, both uses, comparison note).
- **Grammar rules** (`content/ja/grammar/rules.tsv`, matched by `server/langs/ja/grammar.py`): token patterns over the analyser's output, each with the uses its form may have. A plain test is part of the form and not also a word; `[x]` is part of the form and still a word (the verb in お待ちになる); `(x)` is only a condition. Longest first, then most specific. `checks.tsv` holds 140 sentences the rules must get right; a test runs them.
- Not yet: grammar in the plan, grammar placement, the model pass, API, user database, web app.

## Running

From `server/`:

- `uv run python -m pipeline.build` downloads JMdict and Tatoeba into `data/` (gitignored) and writes `data/packs/ja/pack.sqlite`, about 2.5 min. The environment must allow `downloads.tatoeba.org` and `www.edrdg.org`.
- `uv run python -m pipeline.sample` rewrites `tests/fixtures/pack.sqlite` from the built pack.
- `uv run python -m pipeline.coverage`: coverage by number of words known.
- `uv run python -m sim.report`: six months of simulated workload, about 4 min.
- `uv run python -m integrations.wordlist FILE`: imports `word/reading` or `word<TAB>reading` lines, prints coverage and the next words to learn.
- `uv run python -m integrations.renshuu fetch` saves the owner's Renshuu history to `data/renshuu/` (about 30 calls of the 2,000 a day allowed; needs `api.renshuu.org` allowed and the read-only key in the environment variable `read_only_renshuu`). `... renshuu report` replays it and prints coverage.
- `uv run python -m pipeline.grammar` runs the grammar checks, then the rules over the whole library (about 70 s): forms found, the share the model must settle, uses no rule finds, and the particles and endings no rule takes.
- `uv run python -m pipeline.lessons` checks the grammar graph: references, cycles, required fields per kind, and that the seed order lists every item once, after its prerequisites. A test runs the same check.

## Findings

- Tatoeba, words only: the 1,000 most frequent words fully cover 31% of sentences and leave one unknown in another 35%; 5,000 words give 68% and 23%. Ranking by text unlocked barely beats frequency, so the queue ranks by frequency (009).
- Simulated workload: 10 new words a day settles at about 100 reviews a day, 8% failed. A Listener at 15 words a day reaches about 260 and overruns the 200 cap.
- The owner's Renshuu export, 1,437 words: 1,410 matched, 27 guessed, 0 missing; 21.2% of passages fully known, 34.6% with one unknown. The words still missing are mostly grammar the analyser links as words (様 for よう, 下さる for ください, 仕舞う for てしまう, 就く for について) and counters (箇 in 一つ, 度 in 一度). The export is not in the repo; ask the owner to upload it again.
- The owner's full Renshuu history (fetched 31 October 2026): 1,437 words, all matched by JMdict number (four する verbs through their noun); 27,423 review days since June 2024, last on 5 May 2026; 3,247 cards: 1,755 recognize, 1,401 cloze, 91 listen. Six months on, 2,558 cards are due and half the recognize cards are below 70% recall, so 10.1% of passages are fully known and 29.6% have one unknown, against 21.2% and 34.6% when every listed word counted as known.
- Grammar markers in the library, found by the analyser alone (free, 17 s): 39 particles and endings appear in at least 1% of passages, 70 in 0.1%, 108 in 0.01%; は 62%, た 38%, に 35%, を 34%, の 30%, て 28%, だ 28%, が 25%, ます 13%, ない 12%. Patterns by substring: ている about 13% with its contractions, ように 1.5%, ため 1.2%, ことができる 0.5%, てもいい 0.3%. Which use a marker has is what needs the model. Against the seed order, spoken って (2%) and べき (0.7%) sat far later than their frequency and were moved up; the rest of the disagreements are what the computed order is for.
- Grammar rules over the library: 1.15 million forms in 249k passages. Rules settle 38% outright (one use); 62% have several uses for the model to choose from, almost all of them は, を, に, の, が, て, で and と. No rule finds the noun-modifying clauses, the imperative or でも, as intended: those are the model's. The particles and endings no rule takes are all rare (わ 1,071 times, then さ, ぞ, い, なんか, とも, こそ).
- Grammar in the pack: 1,135,768 word occurrences (about 120,000 fewer, the words that grammar forms are made of: いる in ている, こと, できる, 様 for よう, 下さる for ください) and 2.5 million grammar rows, one per possible use. 98.9% of passages hold grammar that is not nuance. With grammar counted and none of it known, the owner's coverage falls to 0.3% fully known and 1.8% with one unknown: placement for grammar is now what the owner's numbers wait on.
- Linking rules found the hard way: lemma before written forms (いる not 射る), a readings table (私 read わたし), kana words by written reading first (いい → JMdict いい), potential verbs fall back to the verb (会えた → 会う). A run of words JMdict lists as one word is one word (お茶, 日本語, 泣き出す), longest first, matched by spelling because sounds change where words join (日曜日); except set phrases (JMdict `exp`, left to the model pass) and counters, which stay with their number.

## Next

1. Grammar (006 to 010), in this order: (a) the owner reads the item list and the ている sample and flags what feels wrong; (b) detection rules over the analyser output, done; (c) grammar in unknowns, done; (c2) grammar in the plan: candidates from the graph with prerequisites, effort per kind, building blocks, the grammar cap and explanation steps (009, 013), a second `core/` change to show the owner first; (c3) grammar placement: mark known what a learner already knows, by a quick check (009) and by mapping the 25 Renshuu grammar points the owner has studied; (d) the 006 test set and the model pass, which only chooses between uses and catches what rules miss; it costs money, so measure on a small sample and ask before the full run; (e) lessons for a first slice by the 010 process.
2. Design. Direction under review: a program built from the materials of a printed technical manual (the owner's references: 1970s US Navy training manuals, an oscilloscope front panel, *A Dictionary of Basic Japanese Grammar*). Type: a Century Schoolbook-style serif (TeX Gyre Schola) for everything in the interface, labels in its true small caps; Mincho for Japanese; draughting lettering (osifont) only inside drawings (chart axes, dimension lines, keys). Uppercase letter-spaced sans labels read as machine-made. Structure is software, not a page: the object being worked on is largest, details beside it (a bottom sheet on phones), one primary action per screen as a black key with a white inset line, secondary actions as small-caps links. Keyboard hints only where a keyboard is in use. Today is the day's work as numbered steps with amounts and progress, not separate number tiles. Separation by space and type, not lines: rules only for the heavy title band (on Review it is the progress bar), tables and notices. Lessons alone keep the page form, with key-sentence tables after the grammar dictionary; on phones those tables turn to one row per part. Text only for news; anything seen twice belongs in a fixed place. Text reads like a legal notice: plain and complete. Black ink; one spot colour only for unknown words and ○/× marks. Rejected: dashboard looks (number tiles, modern grotesques), manual cosplay (captions on everything, prose for data), paper textures, divider lines everywhere. Mockups on the owner's private canvas https://claude.ai/artifact/7R6Yo7NbUwATNX2XHguPyE (rows D and phone current). Fonts: TeX Gyre Schola (GUST Font License, from CTAN, e.g. ctan.math.illinois.edu `fonts/tex-gyre/opentype/`) and osifont (LGPL 3 with font exception, github.com/hikikomori82/osifont via cdn.jsdelivr.net); local copies in `data/fonts/` and uploaded to the canvas. Rows A to C on the canvas are rejected history. Accepted by the owner as an initial sketch; the look will change, so every visual choice must live in tokens and a few primitives, never in screens. Next: tokens and primitives, when the web app starts.
3. API, user database, web app (011).
4. Anki review logs, when someone needs them.

## Open

- Renshuu does not record how an answer was given; multiple choice counts as recall in the import. Kanji (10) and grammar (25) are fetched but not imported until those items exist.
- A learner back from a break: the owner would return to 2,558 due cards. The cap and frequency order handle it, at 200 a day for about two weeks; it may deserve a design of its own.
- Button type: the owner finds the small-caps serif on keys "a bit ridiculous"; revisit once tokens exist.
- Source cap (009): undefined until a second source arrives. As a count it would flatten the top of the ranking, so probably a share.
- Golden outputs per named learner (012) wait until plan behaviour settles; invariants are tested meanwhile.
- Display policy is not enforced yet; Tatoeba allows full display.
- A word marked known counts in every kanji spelling until reviewed. Likewise a recognize card in one spelling (say an imported 子供達) keeps the item's other spellings (子供たち) from ever being offered.
- A compound JMdict lists counts as one unknown word even when its parts are known (経済活動). Rare compounds are where this bites; reading them through their parts needs a way to tell transparent compounds from opaque ones (自転車).

- Lesson sources are fetched with curl (WebFetch cannot resolve those hosts here). The ている lesson has been through all of 010 except the owner's approval: three sources compared in `teiru.notes.md`, checked against them by a second model.
- Grammar or word: a pattern that attaches to any verb, adjective, noun or clause is grammar; an expression built on one content word is a word (似ている, 何も, 一番). Stem compounds with 始める, 終わる, 続ける and 出す stay words because they mean what the verb means; すぎる, やすい and にくい are grammar because they don't.
- Lessons arrive gradually (owner's question, 1 November): every item works from its header alone (name, form, key; detection, unknowns and cards need nothing else), so the app is usable before lessons exist. Until a lesson is written, its page should show the key, library examples and links out to references; lessons are then written in the order learners reach them.
- Until the model pass, a form with several uses splits evenly among them (は counts half topic, half contrast). The model's corpus-wide split replaces this (006).
- Members of a system that are words (こそあど words, counters) have no link to their system yet, so "a system before its members" (009) covers only grammar members.

## Working agreements

- The owner decides what a learner can judge: clarity, workload, how a sample feels. Expertise calls are made with reasons recorded and tested on the owner later. Small reversible choices are made without asking.
- Big decisions get a second opinion from a fresh agent before they are recorded.
- Tests are checked by planting bugs one at a time, with `PYTHONDONTWRITEBYTECODE=1`; a test that misses a plausible bug is fixed.
- Discussion before anything big; small tasks are just done. When the owner asks a question, answer it; build only once they agree.
- The owner's feedback is blunt and meant literally. Fix what they name without overcorrecting elsewhere, and push back with reasons when they seem wrong.
- Replies are plain and short. Each change ends with the decisions it made.
- Before a compaction or a new session, bring this file up to date and push.
- The owner knows about 1,400 words with weak grammar, and their first language, Turkish, shares Japanese sentence structure. They code mostly in C++ and want succinct code and plain explanations.
