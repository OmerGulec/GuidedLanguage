# Proposal: events carry the client's instant

Status: proposed, a change to 013 awaiting the owner's approval. Once approved it becomes part of 013 and this file goes.

**Why.** 013 has the server stamp each event's instant on arrival, and replays history in (instant, id) order with ids made by the client. The client posts events in batches (`docs/v1.md`), which imports, other apps and later offline use all need. Stamped on arrival, every event of a batch gets one instant, so replay orders them by their random ids: a word's review can sort before its introduction, and the scheduler sees no time pass between answers. Posting one event per request would hide the problem in v1 and bring it back with the first offline answer.

**Change.** The client stamps each event when it happens. The server keeps that instant and rejects an event whose instant is more than one minute ahead of its own clock. Imports keep their original instants, as now. The server still gives each event a sequence number, used only as a sync cursor, and records when it arrived.

**Cost.** A client with a wrong clock records wrong instants. Rejecting the future bounds the damage in one direction; a clock running behind makes reviews look earlier than they were, which shortens intervals and is safe. The arrival time is kept so a bad clock can be found and corrected later.

**What does not change.** Replay order, event ids, origins, schema versions, and every function in core: they already take instants as data.
