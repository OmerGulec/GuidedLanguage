# Glossary

One name per concept. Code, comments and documents use these and no synonyms.

| Term | Meaning |
|---|---|
| Item | Something a learner can know. Kinds: kana, word, set phrase, grammar use, formation, system, kanji, kanji reading. A word is one dictionary entry. |
| Grammar use | One form with one use (006). Includes the sentence structures of 008. |
| System | A lesson that explains a system once (007); an item with no cards. |
| Kanji reading | A kanji with one of its readings, offered when a known word uses it. |
| Facet | One side of an item: spelling, reading, meaning, audio, pitch. Declared per language and item kind. |
| Spelling kind | The spelling of an occurrence: one specific kanji spelling, or kana. |
| Card | A subject and a rung, identified as `subject/rung`. The subject is an item, an item in one spelling, or a pair of items for a contrast card. |
| Ladder | The ordered rungs a goal gives an item kind (004). Each rung has a stable name. |
| Goal | What a learner wants to be able to do; chooses the rungs. |
| Situation | What is possible right now: sound, keyboard. |
| Method | How a card was answered: self-graded, typed or multiple choice. |
| Form | An inflection, particle or multi-part pattern. |
| Formation | The skill of building or undoing a form. |
| Pattern | A form made of parts, such as てもいい. |
| Chunk | A pattern known before its parts are. |
| Form page | A form's lesson page: the idea its uses share. A file with a header like an item's, but not an item. |
| Lesson header | The TOML header of an item's lesson file (010); together the headers are the grammar graph. |
| Seed order | The hand-ordered list of grammar items that the computed order is checked against (009). |
| Explanation step | The short "why it means this" shown once a chunk's parts are known. |
| Source | Where passages come from, with license and display policy. |
| Passage | A short self-contained text, identified by a hash of source and normalised text. |
| Occurrence | An item at a span of a passage, in a given spelling, with the probability that it is the item meant: 1 for a word, a share for each possible use of a grammar form. |
| Grammar rule | A token pattern over the analyser's output that finds a form and lists the uses it may have (`content/ja/grammar/rules.tsv`). |
| Modality | Reading or listening. |
| Difficulty | A passage's number of items, then its deepest nesting (008). |
| Event | Something that happened to a learner. Append-only. |
| State | Everything derived from a learner's events. |
| Study day | A local date that starts at the learner's chosen hour. |
| Due | A card is due on a study day when its recall chance would fall below the retention target by the end of that day, or when a lookup made it due. |
| Overdue | Due on an earlier study day and not yet reviewed. |
| Learned | First reviewed. |
| Graduated | Passed on a study day after the one it was learned, or given a starting memory by Marked known. |
| Lapse | A failed review of a graduated card that was not overdue. |
| Known | An item whose first rung has graduated and whose last review did not fail. |
| Re-teaching | Showing a suspended item's lesson again, then resuming its cards. |
| Value | How well a card is held at an instant, from 0 to 1 (013). |
| Unknowns | A passage's expected number of unknown items, per modality (013). |
| Coverage | The share of the library a learner can read, shown as progress; derived from unknowns. |
| Memory | What the scheduler knows about a card: stability, difficulty, phase, due and last review. |
| Mastery | A card's stability: how long its memory lasts without review. |
| New budget | New items per day, re-teaching included. Unlocked rungs get an equal allowance of their own. |
| Pack | The read-only build of one language's library and items. |
| Ranking | Each item's frequency and most common spelling, computed once from a pack. |
| Plan | What a learner does on one study day: reviews, re-teaching, new cards and passages. |
