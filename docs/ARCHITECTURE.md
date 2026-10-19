# Architecture

## Overview

```text
Next.js UI ──REST──▶ FastAPI ──enqueue──▶ Redis/RQ Worker ──subprocess──▶ SimulationCraft
                         │                         │
                         └── PostgreSQL/SQLite ◀────┘
```

Layers are intentionally separated:

1. **UI** — draft build state (Zustand), server state (TanStack Query)
2. **API** — validation, catalog, job orchestration
3. **Game data** — versioned JSON + MID1 presets
4. **Profile composer / APL mutator** — UI config → sanitized `.simc`
5. **Simulation engine** — `ISimulationEngine` (`simc` | `mock`)
6. **Persistence** — jobs, builds, comparisons, cache keys

## Engine interface

`ISimulationEngine.validate_request` / `run` with implementations:

- `SimulationCraftEngine` — production
- `MockSimulationEngine` — UI/dev only (`isDemo=true`)

## Security boundaries

- SimC is never invoked with a shell.
- User APL / imported profiles are allowlisted; `threads`, paths, `armory`, report outputs are stripped.
- Temp directories own all generated files.
- Timeouts and iteration caps bound CPU use.

## Caching

Successful jobs store a SHA-256 of the canonical request + `simcCommit` + `dataSnapshotId`. Identical requests reuse prior results.
