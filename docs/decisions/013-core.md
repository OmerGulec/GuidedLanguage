# 013 — Core definitions

Status: proposed

## Events

Each event has an id made by the client (duplicates are ignored), a server sequence number (used only as a sync cursor), an instant stamped by the server (imports keep their original instant), an origin (ours, Anki, …) and a schema version; old shapes are upgraded in one function. History is replayed in (instant, id) order. Imported events get deterministic ids, so re-importing never duplicates history.

| Event | Meaning |
|---|---|
| Introduced(item, reason) | Met an item: new, re-taught, a chunk's explanation step, or imported. |
| Reviewed(card, passed, method, answer) | A card answered: self-graded, typed or multiple choice. Typed answers are kept. |
| LookedUp(item, passage, surface) | Tapped in the reader. |
| Read(passage, mode) | Finished a passage: read, listen or along. |
| Exercised(passage, kind, passed, answer) | Dictation or a passage question. |
| Missed(item, passage, surface) | "I didn't get this word here." |
| Marked(item, status, reason) | Known, ignored or unknown; by hand, placement or import. |
| Retracted(event) | Undo. |

An import emits Introduced and Reviewed events for the cards it maps; reviews of cards outside the current goals are kept but unused. Settings, accounts and corrections to the shared pipeline are plain rows, not events.

## Settings

One versioned input: scheduler (FSRS via py-fsrs) parameters and version, retention target (default 0.9), time zone, study-day start, and the named settings — new budget, grammar and kanji caps, review cap, effort per item kind, source cap, spacing between cards of one item, lapses before suspension, starting memory for marked items. Defaults live in one settings file. Derivation applies the current settings to the whole history, so changing them is deliberate. Randomness is seeded. Elapsed time is measured between instants.

## Memory

- A card's memory comes only from its self-graded and typed reviews, with one exception: Marked known gives an item's first rung a starting memory as if learned long ago, if it has no reviews. Starting memories are spread so they don't fall due together. Later rungs start fresh.
- LookedUp, Missed and a failed exercise on its clue items make the item's first rung due the next study day. Multiple choice, reading and passed exercises change nothing.
- A lapse is a failed review of a graduated card that was not overdue. After the set number of lapses the card is suspended until the item is re-taught.
- A typed answer that matches another known item records a collision (004).

## Cards

Cards are derived, not created: items introduced or marked known × current goals × ladders (004). A rung unlocks when the rung before it graduates, then waits in the queue (009). After any review of an item, its other cards wait the set spacing; a next-day due from a lookup overrides it.

## Value and coverage

A card's value at an instant:

- 0 if never passed, or if its last review failed;
- 1 if its recall chance is at or above the retention target;
- otherwise its recall chance.

Coverage is computed per modality, evaluated at the next study-day boundary.

- Counted items are words, set phrases, grammar uses and structure items. Kanji, kana and formations have no occurrences. Occurrences inside a pattern's span count only through the pattern.
- A word occurrence takes the highest value among its relevant cards: for reading, its spelling's rung-1 card, or for a kana spelling any card linking sound and meaning (002); for listening, its audio card. With no such card its value is 0.
- A grammar occurrence takes Σ P(use) × the value of that use's card (006).
- Ignored items, nuance items, names and numbers have value 1.
- A passage's coverage is Σ (1 − value) over its distinct items: a word once per spelling kind, a form once at its lowest value.

A pattern is known as a chunk while it is known but its parts aren't; it is understood once its parts are known and its explanation step is done.

**Mastery** is a card's stability: shown per direction on item pages and as a distribution on progress screens.

## Plan

1. Due cards the situation allows, up to the review cap; beyond it, the most frequent items first and the rest wait.
2. Re-teaching, then new cards from the queue (009) up to the new budget.
3. Reading: the passages with the fewest expected unknowns, then by difficulty (008).

## Functions

`derive(events, pack, goals, settings) → state` · `values(state, pack, at) → values per modality` · `coverage(values, pack) → expected unknowns per passage` · `queue(state, pack, goals, settings) → items` · `plan(state, coverage, pack, goals, situation, settings, day) → today` · `review(memory, passed, at, settings) → memory`

The simulator (012) uses a memory model different from the scheduler's, so tests don't check the scheduler against itself.
