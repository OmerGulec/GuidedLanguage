# 006 — Grammar items and detection

Status: accepted

**Teaching.** A grammar item is one form with one use: ている-ongoing and ている-resulting-state are separate items, taught at different times. A form's page shows only the uses already taught, plus how many more are coming. Uses that don't change understanding are merged. Fixed expressions with one meaning (似ている, と考えられる) are vocabulary.

**Detection.** Every passage goes through one offline pass when it is added: the analyser splits it, then a language model checks the word links, finds grammar forms (including multi-word forms and contractions) and gives each a probability per use, or says it is unsure. Hand-written rules are added only where they measurably help or save cost.

**Probabilities.** Each grammar occurrence carries a probability per use, summing to 1. An unsure label is spread by the form's corpus-wide split. Unknowns use them as in 013.

**Display.** The reader names a use only when confident; otherwise it lists the possible uses the learner has been taught.

**Measurement.** A test set of real sentences, about 50 per use, drawn from several kinds of writing. Two different models label it; where they agree the label stands, where they disagree the sentence counts as unsure until someone who can judge Japanese grammar reviews it. Until then, measured accuracy is optimistic, since both models can be wrong together. Per use, it measures how often a named use is right and how many instances are caught, and it calibrates the model's confidence. It stays as a permanent check on every pipeline change. The final measure is how much errors change passages' unknowns.

**Corrections.** A "this looks wrong" report in the reader feeds a shared correction list that overrides the pipeline.
