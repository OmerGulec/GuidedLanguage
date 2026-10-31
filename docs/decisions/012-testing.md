# 012 — Testing with simulated learners

Status: accepted

**Simulator.** A seeded simulator plays a learner against the real core over simulated days: it answers cards with a success chance from a simple memory model, reads passages, looks words up and imports history. State is derived from events and core takes time as input, so a learner state is just a seeded event log.

**Named states.** Fixed seeds produce named learner states on the fixture pack: day 0, kana done, the owner's profile (about 1,000 imported words, weak grammar), three months in, a heavy user. Tests run against them, and the dev server can start as any of them.

**Time travel.** In development the clock can be moved forward by days, with the simulator answering whatever falls due, so any screen can be checked at any point of a learner's path. The same runs show workload: daily reviews over months for given settings.

**Three kinds of test.**

- Behaviour: properties of the pure core (replaying events is deterministic; learning an item never raises a passage's expected unknowns) and golden outputs per named state (today's plan, queue order, coverage).
- Architecture: dependency layers, display policy, ID resolution.
- The running app: Playwright drives each screen in each named state and saves screenshots for review.

**Test quality.** Every test must be able to fail for a plausible bug. Mutation testing runs occasionally to check that tests catch real changes.
