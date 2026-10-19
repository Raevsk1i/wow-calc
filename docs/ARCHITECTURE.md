# Architecture

## Overview

```text
Next.js UI ──REST──▶ FastAPI
                       ├─ FastEstimateEngine (deterministic)
                       └─ enqueue ──▶ Redis/RQ Worker ──subprocess──▶ SimulationCraft
                                              │
                                              └── PostgreSQL/SQLite
```

Layers:

1. **UI** — draft build state (Zustand), server state (TanStack Query), RU 3-column layout
2. **API** — validation, SpecRegistry, job orchestration, document-shaped routes
3. **Game data** — versioned JSON catalog + MID presets + ruleset provenance
4. **Profile composer / APL mutator** — UI config → sanitized `.simc`
5. **Simulation engines** — `fast_estimate` | `simc` | `mock`
6. **Persistence** — jobs, builds, comparisons, cache keys

## Engine interface

`ISimulationEngine.validate_request` / `run` with implementations:

- `FastEstimateEngine` — deterministic approximation
- `SimulationCraftEngine` — Accurate Monte Carlo (production)
- `MockSimulationEngine` — UI/dev only (`isDemo=true`)

## Security boundaries

- SimC is never invoked with a shell.
- User APL / imported profiles are allowlisted; `threads`, paths, `armory`, report outputs are stripped.
- Temp directories own all generated files.
- Timeouts and iteration caps bound CPU use.

## Caching

Successful Accurate jobs store a SHA-256 of the canonical request + `simcCommit` + `dataSnapshotId`. Identical requests reuse prior results.
