# 004 — Study model

Status: accepted

**Goals.** Learners pick outcomes, not cards: Reader, Listener, Kanji, Complete. Each preset turns on rungs of the ladders below; custom goals pick rungs freely behind an advanced screen. A learner who always reviews without sound can choose `recognize` in the kana spelling there.

| Item kind | Rungs in order, with stable names (presets that include them) |
|---|---|
| Word, set phrase | 1. `recognize`: spelling → {reading, meaning} (all) · 2. `listen`: audio in a sentence → meaning (Listener, Complete) · 3. `cloze`: type the word into a sentence (Complete) · 4. `pitch`: audio → pitch (Complete) |
| Kana | 1. `read`: kana → sound (all) · 2. `hear`: audio → kana (Listener, Complete) |
| Grammar use | 1. `sentence`: sentence → meaning (all) · 2. `cloze`, typed (Complete) |
| Formation | 1. `undo`: form → dictionary form (all) · 2. `build`: dictionary form → form, typed (Complete) |
| Kanji | 1. `meaning`: kanji → meaning (Kanji, Complete) |
| Kanji reading | 1. `reading`: a known word with the kanji → that kanji's reading (Kanji, Complete) |
| Contrast (a pair of items) | 1. `contrast`: both items → the difference (all) |
| System | none |

**Situation.** Sound and keyboard are remembered per device. Cards the situation rules out wait; they are not failed. Stand-ins come later, and never count toward the card they replace.

**A new word** is met in a sentence where it is the only unknown, with audio, then repeated in the same session on its first rung. Later rungs and spacing follow 013.

**Prompts.**

- Recognition shows the word alone, with a fresh real sentence on the back. Words that share a spelling with another word show a sentence on the front.
- Production is a cloze in a sentence, never L1 → word.
- Listening plays the word inside a short sentence. Most listening practice happens on passages.
- Grammar use: a real sentence where everything else is known; say what it means. The back shows a translation and the key point. The form is highlighted until the card graduates. Translations are made offline by a model and checked like grammar labels (006).
- Formation: a known verb in a form, back to its dictionary form. A different verb each review, favouring tricky ones.
- Contrast: a confusable pair side by side; say the difference.

**Grading.** Pass or fail only. The rules are fixed beforehand per card type, and only the points on the back count: word, reading and main meaning; formation, the exact dictionary form; grammar use, the key point; contrast, both sides. When in doubt, it's a fail. Typed answers are checked automatically.

**Collisions.** Look-alikes are where knowing gets tested. Pairs come from shape (待/持), sound (期間/機関), meaning (暑い/熱い), grammar form (ている/てある) and the learner's own mistakes (a typed answer that is another known item). A new item is introduced next to the known items it most resembles. Once both items of a pair are known, a contrast card tests them together.

**Spellings and readings.** A word is learned in its most common spelling and reading, counted in our library. Other spellings get their own card only when common enough to rank in the queue; rare ones are labelled as variants. Other readings are shown and accepted.

**Senses.** Tracked per word. Set phrases are their own items. Cards per sense come once occurrences carry senses.

**Kanji.** Optional. "Through words only" shows information but never drills. Ranking is in 009. Kanji readings are offered only when a known word uses them. Readings that belong to a whole word (大人 おとな) don't count; sound changes group under the base reading.

**Upkeep.** Suspension and re-teaching follow 013. Anything can be marked known or ignored.

**Not in v1.** Speaking, handwriting, stand-ins.
