# 006 — Grammar items and detection

Status: accepted

**Teaching.** A grammar item is one form with one use: ている-ongoing and ている-resulting-state are separate items, taught at different times. A form's page shows only the uses already taught, plus how many more are coming. Uses that don't change understanding are merged. Fixed expressions with one meaning (似ている, と考えられる) are vocabulary.

**Detection.** Every passage goes through one offline pass when it is added: the analyser splits it, then a language model checks the word links, finds grammar forms (including multi-word forms and contractions) and gives each a probability per use, or says it is unsure. Hand-written rules are added only where they measurably help or save cost.

**Coverage.** A grammar occurrence counts as understood when the uses the learner knows hold at least 80% of its probability.

**Display.** The reader names a use only when confident; otherwise it lists the possible uses the learner has been taught.

**Measurement.** A test set of real sentences, about 50 per use, drawn from several kinds of writing and labelled by someone who can judge Japanese grammar. Per use, it measures how often a named use is right and how many instances are caught, and it calibrates the model's confidence. It stays as a permanent check on every pipeline change. The final measure is how often an error flips a passage between readable and not.

**Corrections.** "I didn't get this" in the reader feeds a correction list that overrides the pipeline.
