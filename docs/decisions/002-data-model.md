# 002 — Data model

Status: accepted

| Concept | Meaning |
|---|---|
| Item | Something a learner can know: word, set phrase, grammar pattern, kanji. A word is a dictionary entry, not a string. |
| Facet | One side of an item: written form, reading, meaning, audio, pitch. Each language declares its own. |
| Source | Where passages come from, with its license and display policy. |
| Passage | A short self-contained text, paragraph-sized. |
| Occurrence | Item X appears in passage P at span S. Spans may overlap. |
| Event | Something happened: review, lookup, passage read, manual mark. Append-only, tagged with origin (ours, Anki, Renshuu, …). |
| State | Derived from events. Never the source of truth. |

Rules:

- A passage is understood only when every item covering it is known.
- A test is an item plus a direction (prompt facet → answer facet). Scheduling is per direction.
- State distinguishes *known as a chunk* from *understood*, so items can be met before they are explained.
- Core code never imports language-specific code.
