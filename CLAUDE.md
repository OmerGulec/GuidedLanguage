# Working on GuidedLanguage

Decisions live in `docs/decisions/`. Read the ones your change touches before writing code.

## Code

- Code explains itself. Names say what a thing is in the domain. No names or comments that refer to a conversation, a task, a ticket or anything else the reader would have to look up.
- Comments are rare and say why, never what. Write them the way maintainers of a mature, respected codebase do. Avoid verbosity.
- Names are full words and short. One name per concept (see Glossary), no synonyms.
- Before adding to a function or file, ask whether the result is professionally acceptable. If it isn't, refactor first.
- No speculative abstraction. Interfaces exist only at the seams named in 011.
- No new dependency without the owner's approval.
- Python follows 003.

## Errors

- Expected outcomes are part of the return type: `X | None`, or a closed union of result types handled with an exhaustive `match`.
- Exceptions are for bugs and I/O failures. They are caught only at the edge of the shell (API handlers, pipeline steps), never inside `core/`.
- Web: expected outcomes are in the response type; network failures throw and are handled in one place.

## Tests

- A test must be able to fail for a plausible bug. Tests that restate the code or can't fail are not written.
- Behaviour, architecture and the running app are all tested (012).
- Learner states come from the simulator (012), never from hand-built rows.
- Never run paid commands: `eval`, pipeline model passes.

## Working

- One feature: one short spec, one folder.
- Don't change `core/`, the dependency rules or `docs/decisions/` without the owner's approval.
- End each change with a short list of the decisions it made.
- Commits are small and say why.

## Glossary

| Term | Meaning |
|---|---|
| Item | Something a learner can know: word, set phrase, grammar use, kanji, kana. |
| Facet | One side of an item: spelling, reading, meaning, audio, pitch. |
| Card | A subject (item, sense or pair), a prompt facet and a set of answer facets. |
| Form | An inflection, particle or multi-part pattern. |
| Use | One function of a form. A grammar item is one form with one use. |
| Formation | The skill of building or undoing a form. |
| Source | Where passages come from, with license and display policy. |
| Passage | A short self-contained text. |
| Occurrence | An item at a span of a passage, in a given spelling. |
| Event | Something that happened to a learner. Append-only. |
| State | Everything derived from a learner's events. |
| Pack | The read-only build of one language's library and items. |
| Goal | What a learner wants to be able to do; decides their cards. |
| Situation | What is possible right now: sound, keyboard. |
| Coverage | A passage's expected number of unknown items, per modality. |
| Mastery | A card's stability: how long its memory lasts without review. |
