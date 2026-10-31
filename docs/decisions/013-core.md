# 013 — Core definitions

Status: accepted

Terms are defined in `docs/glossary.md`.

## Events

Each event has an id made by the client (duplicates are ignored), a server sequence number (used only as a sync cursor), an instant stamped by the server (imports keep their original instant), an origin (ours, Anki, …) and a schema version; old shapes are upgraded in one function. History is replayed in (instant, id) order. Imported events get deterministic ids, so re-importing never duplicates history.

| Event | Meaning |
|---|---|
| Introduced(item, reason) | Met an item: new, re-taught, an explanation step, or imported. |
| Reviewed(card, passed, method, answer) | A card answered. Typed answers are kept. |
| LookedUp(item, passage, surface, context) | Tapped in the reader. |
| Read(passage, modality) | Finished a passage. |
| Exercised(passage, kind, passed, answer) | Dictation or a passage question. |
| Missed(item, passage, surface, context) | "I didn't get this word here." |
| Marked(item, status, reason) | Known, ignored or unknown; by hand, placement or import. |
| Retracted(event) | Undo. |

An import emits Introduced and Reviewed events for the cards it maps; reviews of cards outside the current goals are kept but unused. Settings, accounts and corrections to the shared pipeline are plain rows, not events.

## Settings

One versioned input: scheduler (FSRS via py-fsrs) parameters and version, retention target (default 0.9), time zone, study-day start, and the named settings: new budget, grammar cap, kanji cap, review cap, reading per day, effort per item kind, source cap, spacing between cards of one item, lapses before suspension, starting memory and spread for marked items. Defaults live in one settings file. Derivation applies the current settings to the whole history, so changing them is deliberate. Randomness is seeded. Elapsed time is measured between instants.

## Memory

- A card's memory comes only from self-graded and typed reviews, with one exception: Marked known gives an item's first rung a starting memory as if learned long ago, if it has no reviews, and that card counts as graduated. Starting memories are spread evenly over the set period in a seeded order. Later rungs start fresh.
- Marked unknown undoes an earlier mark; reviews are kept, and an item never introduced returns to the candidates.
- LookedUp, Missed and a failed exercise on its clue items make the item's first rung due the next study day. Multiple choice, reading and passed exercises change nothing.
- After the set number of lapses since it was last re-taught, a card is suspended. Re-teaching resumes it with its memory kept and makes it due.
- A typed answer that matches another known item records a collision (004).

## Cards

Cards are derived, not created: items introduced or marked known × current goals × ladders (004). The first rung in the learner's goals is available when the item is introduced; each later one unlocks when the previous one in the goals graduates, then waits among the candidates (009). After any review of an item, its other cards wait the set spacing; a due set by a lookup overrides it.

## Value and unknowns

A card's value at an instant:

- 0 if it has no memory, or if its last review failed;
- 1 if its recall chance is at or above the retention target;
- otherwise its recall chance.

Unknowns are computed per modality, at the next study-day boundary.

- Counted items are words, set phrases and grammar uses. Kana, kanji, kanji readings, formations and systems have no occurrences. Occurrences inside a pattern's span count only through the pattern.
- A word occurrence takes the highest value among its relevant cards. Reading: the `recognize` card for its spelling; for a kana spelling, any card that links sound and meaning (`recognize` in any spelling, `listen`). Listening: its `listen` card. With no such card its value is 0, so a rare spelling stays unknown until it earns a card.
- A grammar occurrence takes Σ P(use) × the value of that use's `sentence` card (006).
- Ignored items, nuance items, names and numbers have value 1.
- A passage's unknowns are Σ (1 − value) over its distinct items: a word once per spelling kind, a form once at its lowest value.

A pattern is a chunk while it is known but its parts aren't; its explanation step comes once its parts are known.

**Mastery** is a card's stability, shown per card on item pages and as a distribution on progress screens.

## Plan

1. Due cards the situation allows, up to the review cap (overflow order in 009).
2. Explanation steps, re-teaching and candidates until the new budget is spent (009).
3. Reading: the set number of passages (009), in the modalities the goals and situation allow. A passage may carry an exercise: dictation when typing is possible, questions where they exist (008).

## Functions

`derive(events, pack, goals, settings) → state` · `values(state, pack, settings, at) → values per modality` · `unknowns(values, pack) → per passage` · `candidates(state, pack, goals, settings) → ranked candidates` · `plan(state, unknowns, pack, goals, situation, settings, day) → today` · `review(memory, passed, at, settings) → memory`

The simulator (012) uses a memory model different from the scheduler's, so tests don't check the scheduler against itself.
