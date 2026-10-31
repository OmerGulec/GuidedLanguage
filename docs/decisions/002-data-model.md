# 002 — Data model

Status: accepted

The concepts are defined in `docs/glossary.md`. This record holds the rules about them.

- A word is one dictionary entry, not a string. An occurrence records the spelling it uses.
- A kanji spelling counts only through its own card. A spelling that writes the sound directly (Japanese kana) counts through any card linking the word's sound and meaning. Knowing what a spelling means does not imply knowing how it sounds. The computation is in 013.
- A learner's history is events only; everything else is derived (013).
- A pattern can be known as a chunk before its parts, so it can be met before it is explained (013).
- Core code never imports language-specific code.
