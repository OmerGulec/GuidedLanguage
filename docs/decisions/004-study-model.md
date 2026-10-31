# 004 — Study model

Status: accepted

**Goals.** Users pick outcomes, not cards: Reader, Reader + Listener, Kanji learner, Complete. Each preset derives its cards; a custom set sits behind an advanced screen.

**Situation.** Sound and keyboard are remembered per device. Cards the situation rules out wait; they are not failed.

**Stand-ins.** kana → meaning may stand in for audio → meaning while sound is off. A stand-in never counts toward the card it replaces and pushes that card back a few days. The backlog is capped and ordered by unlock value; the app shows when listening was last tested.

**A new word.**

1. Met in a sentence where it is the only unknown, with audio.
2. Same-session repeats on the easiest card in the user's goals.
3. Harder cards unlock once easier ones hold, and spend the same daily budget as new words.
4. After any review of a word, its other cards wait a few days.

**Prompts.**

- Recognition shows the word alone, with a fresh real sentence on the back. Words that share a spelling with another word show a sentence on the front.
- Production is a cloze in a sentence, never L1 → word.
- Listening plays the word inside a short sentence. Most listening practice happens on passages.
- Grammar use: a real sentence where everything else is known; say what it means. The back shows a translation and the key point. The form is highlighted at first; highlighting stops once the card is stable. Translations are made offline by a model and checked like grammar labels (006).
- Formation: a known verb in a form, back to its dictionary form. A different verb each review, favouring tricky ones.
- Contrast: a confusable pair side by side; say the difference.

**Spellings and readings.** A word is learned in its most common spelling and reading, counted in our library. Other spellings get their own card only when common enough to rank in the queue; rare ones are labelled as variants. Other readings are shown and accepted.

**Senses.** Tracked per word. Set phrases are their own items. "I didn't get this word here" in the reader creates a card for that sense.

**Kanji.** Optional. "Through words only" shows information but never drills. "Kanji as items" queues a kanji once it appears in enough known words, weighted by misses. Readings are (kanji, reading) pairs, taught only when a known word uses them. Readings that belong to a whole word (大人 おとな) don't count; sound changes group under the base reading.

**Grading.** Pass or fail only. The rules are fixed beforehand per card type, and only the points on the back count: word, reading and main meaning; formation, the exact dictionary form; grammar use, the key point; contrast, both sides. When in doubt, it's a fail. Production is typed and checked automatically.

**Collisions.** Look-alikes are where knowing gets tested. Pairs come from shape (待/持), sound (期間/機関), meaning (暑い/熱い), grammar form (ている/てある) and the learner's own mistakes (a wrong answer that is another known item). A new item is introduced next to the known items it most resembles. Once both items of a pair are known, contrast cards test them together.

**Upkeep.** Repeated failures suspend a card and re-teach it. Anything can be marked known or ignored.

**Not in v1.** Speaking, handwriting.

**Chunks.** What happens once a chunk's grammar is taught: see 007.
