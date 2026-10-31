# 011 — Architecture

Status: accepted

**Two halves.** An offline pipeline builds a *pack*: a folder with one read-only SQLite file (items, passages, occurrences, translations, language facts such as which spellings write the sound) and the occurrence matrices as `.npy` files the server memory-maps. The server loads a pack and keeps users' data in a separate SQLite database. Everything a user sees is derived from the pack and the user's events.

**Stable IDs.** Words are JMdict entry numbers; kanji and kana their characters; grammar items authored IDs. Passages are a hash of source and normalised text. Reader events carry the item ID plus surface form and context, never offsets alone. A lesson header's `replaces:` and the pack's `id_map` say where history goes when an item is split, merged or renamed. The server refuses a pack in which any ID referenced by an event fails to resolve.

**Pure core, thin shell.** `core/` is pure functions over frozen dataclasses: no I/O, no clock (`now`, timezone and day boundary are inputs), no language-specific code. Only the shell touches disk, network and time. Core is designed by hand, one change at a time, with the owner's approval; agents don't grow it.

```
docs/decisions/      decisions
content/ja/          lessons and comparison notes
server/
  core/              domain, pure
  langs/ja/          analyser, model prompts, pack facts
  pipeline/          sources → pack
  store/             SQLite, one file per feature
  integrations/      anki/, renshuu/
  api/               FastAPI, one file per feature
web/                 Svelte 5, SvelteKit in single-page mode
  src/ui/            tokens and primitives; the only styling
  src/langs/ja/      kana input (wanakana)
  src/features/      today/ library/ dictionary/ you/ reader/ review/
  src/api/           generated types (build output)
CLAUDE.md            agent rules and glossary
```

**Rules enforced by tools.** import-linter layers for Python: `core` ← `langs`, `store` ← `pipeline`, `integrations`, `api`; languages come from an explicit table. ESLint `no-restricted-imports` for web: features import `ui`, `api` and `langs`, never each other. Each feature adds its own route folder, so there is no shared route table. Generated API types are build output; CI fails if they are stale.

**Data.** SQLite in WAL mode with a busy timeout, plain synchronous endpoints. Events hold learning history only; settings and accounts are plain rows. Migrations: `PRAGMA user_version` plus numbered SQL files. Packs are rebuilt, never migrated. The user database is backed up continuously (Litestream): events are the only data that can't be rebuilt.

**Pipeline.** Model outputs are cached by passage hash, prompt version and model, and requested through batch APIs, so a rebuild pays only for what changed. The analyser also runs inside the server for dictionary search with inflected input and, later, for user-supplied text as a background job.

**Audio.** Files named by a hash of text, voice and engine, stored outside SQLite and served with long cache lifetimes. Generated for words and for passages actually served.

**Display policy** is enforced in one serialiser with one test: text licensed for analysis only never leaves the server.

**Auth.** The server serves the built web app from the same origin. httpOnly session cookies stored in SQLite; argon2 password hashes.

**Tests.** A small fixture pack in the repo; property tests that replaying events is deterministic and idempotent; a golden test fixing the planner's order. The 006 accuracy set runs as a separate, paid `eval` command, with results stored per pack version. Agents never start paid runs.

**Secrets.** A `.env` read only by the pipeline. The server needs no model key in v1.

**Deployment.** One VM, Caddy, systemd. Logs time the plan and unknowns endpoints.

**Licences.** JMdict and KANJIDIC2 are CC BY-SA and are credited in the app.
