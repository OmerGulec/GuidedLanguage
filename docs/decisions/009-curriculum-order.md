# 009 — Curriculum order

Status: accepted

All ranking lives here.

**Candidates.** Items not yet introduced, marked known or marked ignored; rungs that have just unlocked; contrast cards whose two items are both known. Kana come first and are the only candidates until all are introduced.

**Rank.** A candidate's frequency is the number of library passages containing its item, each source counting at most the source cap; a grammar use counts a passage by its highest probability there. Rank is frequency divided by the effort for its item kind. Ties break by id. A smarter ranking replaces this only after beating it in the simulator (012).

**Kanji and kanji readings** rank by Σ (1 + lapses) over the learner's known words that contain them.

**Hard edges.** An item is a candidate only once its prerequisites are known (systems: introduced). Prerequisites are the authored ones in lesson headers (010), plus: a form after what it is derived from (007), a pattern after its parts unless its lesson says it is met as a chunk, a system before its members, a formation before the uses built on it.

**Building blocks** (formations, systems) take the rank of their highest-ranked dependent.

**Filling the day.** Explanation steps and re-teaching first, then candidates in rank order until the new budget is spent. Each candidate takes one slot. Grammar uses, formations and systems share a grammar cap; kanji and kanji readings a kanji cap.

**Overdue reviews** beyond the review cap: cards of the most frequent items first.

**Reading** offers passages with the lowest unknowns, then the lowest difficulty, skipping passages already read and those whose display policy forbids it.

**The graph.** Grammar items, their parts and edges are authored data (010), seeded from a hand-ordered beginner list with vocabulary moved to words and the grammar natural text needs added: てしまう, ようだ/みたい/らしい, はず, わけ, ため, ように, ところ, ばかり, honorific and humble verbs, and the structures of 008.

**Placement.** Systems and structures can be passed with a quick check, so learners whose first language already works this way (Turkish, Korean) skip them.

**Check.** The computed order is compared with the hand-ordered list; large disagreements are reviewed before use.
