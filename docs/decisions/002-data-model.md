# 002 — Data model

Status: accepted

| Concept | Meaning |
|---|---|
| Item | Something a learner can know: word, set phrase, grammar pattern, kanji, kana. A word is one dictionary entry, not a string. |
| Facet | One side of an item: spelling, reading, meaning, audio, pitch. Declared per language and item kind. |
| Card | An item, a prompt facet and a set of answer facets, e.g. 分かる → {reading, meaning}. One memory state per card. |
| Source | Where passages come from: work or site, author, genre, license, display policy. |
| Passage | A short self-contained text, paragraph-sized, with its position in the source. |
| Occurrence | Item X appears in passage P at span S, in spelling W. Spans may overlap. May later carry a sense. |
| Event | Something happened: review, lookup, passage read, manual mark. Append-only, tagged with origin (ours, Anki, …) and answer method. |
| State | Derived from events. Never the source of truth. |

Rules:

- A passage is understood only when every occurrence in it is understood.
- An occurrence is understood when its spelling → meaning is known. For a spelling that writes the sound directly (Japanese kana), knowing the word's sound is enough: any spelling → {reading, meaning}, audio → meaning, or kana → meaning. Knowing what a spelling means does not imply knowing how it sounds.
- Only recall updates memory. Multiple choice, reading and lookups are events, never grades.
- State distinguishes *known as a chunk* from *understood*, so items can be met before they are explained.
- Core code never imports language-specific code.
