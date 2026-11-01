# Proposal: the passage a card shows

Status: proposed, a change to `core/` awaiting the owner's approval. Once approved it becomes part of 013 and this file goes.

**Why.** Every card in v1 shows a library passage (`docs/v1.md`, Cards): the back of a word card, the front of a grammar card, the sentence a new word is met in. Core plans which cards are due but not what they show, and what they show depends on the learner's state: "everything else is known" is a fact about this learner today. So the choice belongs in core, next to unknowns.

**The function.** `passage_for(card, unknowns, values, pack, shown, eligible) → passage | None`, in a new `core/passages.py`. It is pure: the plan's values and unknowns at the next study-day boundary go in, one passage id or nothing comes out.

- `eligible` is one flag per passage, made by the shell: the passage has a translation and its source's display policy lets it be shown. Core knows neither translations nor licences, and needn't.
- `shown` is the passages this item has already shown, oldest first, from the learner's state.

**Which passages qualify.** The passage is eligible and holds the card's column: for `recognize` in a kanji spelling, that spelling; in kana, the word in any kana spelling. For a grammar use, the use must also be settled there: probability 0.9 or more. Today only rules and labels settle a use; the model pass will add its confident labels later, through the same number.

**Which one wins,** compared in this order:

1. Everything else known: the passage's unknowns less the card's own share are below 0.5, that is, less than half an unknown item expected.
2. Not shown for this item before; failing that, shown longest ago. So reviews go through different passages before any repeats.
3. Fewest other unknowns.
4. Fewest items, so shorter passages first.
5. Library order, so the choice is deterministic.

A word's first meeting uses the same rule: its own value is 0, so rule 1 asks for a passage where it is the only unknown (004). When no passage meets rule 1, the best of the rest is shown.

**What else changes in core.**

- `Introduced` and `Reviewed` carry the passage shown, or none (old events, imports). The event schema version goes up; older shapes upgrade with none.
- State keeps, per item, the passages it has shown, oldest first.
- A grammar use with no settled, eligible passage is not offered as a candidate: a sentence card can't be made without one. It waits until labels or the model settle one. Without this, は as topic would be offered on day one with nothing to show.

**What does not change.** The pack's core part, values, unknowns, the plan's order and the memory model. Formation cards (`undo`) need verbs in their forms, which the pack doesn't hold yet; they come as a second, smaller proposal once it does.

**Outside core, no approval needed.** The pipeline gives a labelled sentence's use probability 1 and the form's other uses 0, overriding the shares there. That is how the 006 test set settles uses in v1.

**Tests,** against simulated learners (012): the passage always holds the card's column and is eligible; a grammar use's passage is settled; a passage with nothing else unknown beats one with something unknown; repeated reviews of one card go through every qualifying passage before repeating one; a use with no settled passage is never offered; with no qualifying passage the answer is none, never an arbitrary passage.

**Numbers this fixes,** as named constants in `core/passages.py`: settled at 0.9; everything else known below 0.5 unknowns.
