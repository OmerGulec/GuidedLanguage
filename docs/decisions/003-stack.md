# 003 — Stack

Status: accepted

**Server.** Python. Holds all logic: text analysis, scheduling, sync, API.

**Client.** Svelte 5 with strict TypeScript. Displays and sends answers; no learning logic. Its types are generated from the server's API schema.

**Platforms.** One responsive web app, installable as a PWA. Native wrappers (Tauri) later, only if they earn their place.

Python rules:

- uv for packages and environments, ruff for lint and format, pyright in strict mode (ty once it reaches 1.0).
- pydantic, in strict mode, only where data enters from outside: API, imports, config. Inside, frozen dataclasses.
- Variants are closed unions handled by an exhaustive `match` with `assert_never`.
- Seams are `Protocol`s. No inheritance hierarchies.
- Banned: `Any`, `getattr`/`setattr`/`hasattr`, dynamic imports, mutable globals, pass-through `**kwargs`, metaclasses.
