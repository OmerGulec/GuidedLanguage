# 013 — Core definitions

Status: proposed

**Events.** Each event has an id made by the client (duplicates are ignored), a server sequence number (used only as a sync cursor), an instant stamped by the server (imports keep their original instant), an origin (ours, Anki, …) and a schema version (old shapes are upgraded in one function). Memory is replayed in (instant, id) order. Imported events get deterministic ids, so re-importing never duplicates history.

| Event | Meaning |
|---|---|
| Introduced(item, reason) | Met an item: new, re-taught after repeated failures, or a chunk's explanation step. |
| Reviewed(card, passed, method, answer) | A card answered: self-graded, typed or multiple choice. Typed answers are kept. |
| LookedUp(item, passage, surface) | Tapped in the reader. |
| Read(passage, mode) | Finished a passage: read, listen or along. |
| Exercised(passage, kind, passed, answer) | Dictation or a passage question. |
| Missed(item, passage, surface) | "I didn't get this word here." |
| Marked(item, status, reason) | Known, ignored or unknown; by hand, placement or import. |
| Retracted(event) | Undo. |

Settings, accounts and corrections to the shared pipeline are plain rows, not events.

**Effects.**

- Only self-graded or typed reviews change memory. Multiple choice, reading and exercises never do.
- LookedUp, and a failed exercise on its clue items, make an item's cards due the next study day.
- Missed creates a card for that sense.
- Marked known gives the item's cards a memory as if learned long ago, so they return for a check once they would have faded. Ignored items never block and are never reviewed.
- A lapse is a failed review after a card's first study day. Repeated lapses suspend the card until the item is re-taught.
- A typed answer that matches another known item records a collision (004).

**Settings input.** Scheduler parameters and version, retention target, time zone and study-day start form one versioned input. Randomness is seeded. Elapsed time is measured between instants, not study days.

**Cards** are derived, not created: introduced items × current goals × the ladder (004). A card is a subject, a prompt and answers; the subject is an item, an item's sense, or a pair of items for contrast. The next rung unlocks once a card is on schedule, spending the daily new budget.

**Value.** Each card has a value:

- 0 if never passed, or if its last review failed;
- 1 if on schedule, meaning its recall chance is at or above the retention target;
- otherwise its recall chance.

An occurrence takes the value of its relevant card (002). A grammar occurrence takes Σ P(use) × value of that use's card; an unsure label follows the form's corpus-wide split. Ignored items, nuance items, names and numbers have value 1. A pattern is known as a chunk while its own card has value but its parts don't; it is understood once its parts do and its explanation step is done.

**Coverage** of a passage, per modality, is its expected number of unknown items: Σ (1 − value) over its distinct items, evaluated at the next study-day boundary. About 1 means one new item.

**Mastery** of a card is its stability. Item pages show it per direction; progress shows its distribution.

**Queue.** Items not yet introduced whose hard prerequisites are met, ranked by how often they appear in the library (once per passage, each source capped; grammar by Σ P(use)), divided by effort. Building blocks rank with their cheapest dependent. Ties break by id.

**Plan.** Due cards the situation allows, the rest waiting, with a few days between cards of the same item; then new items from the queue up to the daily load limit and grammar cap; then reading: passages with about one expected unknown or fewer, ordered by difficulty.

**Functions.** `derive(events, pack, goals, settings) → state`; `values(state, pack, at) → per modality`; `coverage(values, pack) → expected unknowns per passage`; `queue(state, pack, goals) → items`; `plan(state, coverage, pack, goals, situation, settings, day) → today`; `review(memory, passed, at, settings) → memory`.

**Simulator** (012) uses a memory model different from the scheduler's, so tests don't check the scheduler against itself.
