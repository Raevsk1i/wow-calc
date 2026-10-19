# WoW DPS Lab

Interactive DPS laboratory for **World of Warcraft: Midnight, patch 12.1.5 (Retail)**.

Full catalog coverage: **13 classes / 40 specializations** (including tanks, healers, Devourer, Augmentation). Combat results are produced by **SimulationCraft** (GPL-3.0) via a sandboxed CLI worker — not by invented damage coefficients.

Pinned ruleset: `12.1.5` + client build `70448` + hotfix `2026-10-17` + SimC `d91a570`.

> Not affiliated with Blizzard Entertainment.

## Stack

| Layer | Tech |
|---|---|
| Web | Next.js, React, TypeScript, Tailwind, Zustand, TanStack Query, Recharts |
| API | FastAPI, Pydantic v2, SQLAlchemy |
| Jobs | Redis + RQ |
| Engine | Pinned SimulationCraft (`engine/simc/SIMC_PIN`) |
| Data | Versioned catalog + MID2 presets (MID1 fallback) under `packages/game-data` |

## Quick start (local)

### 1. Build SimulationCraft

```bash
./engine/simc/build.sh
```

### 2. API dependencies

```bash
cd apps/api
python3 -m pip install -e ".[dev]"
```

### 3. Redis

```bash
redis-server --daemonize yes
```

### 4. API + worker

```bash
# terminal A
cd apps/api
uvicorn app.main:app --reload --port 8000

# terminal B
cd apps/worker
PYTHONPATH=../api python3 worker.py
```

For a local sync path without the worker (useful for demos):

```bash
# POST /api/v1/simulations?sync=true runs in-process
```

Or use the mock engine for UI-only work:

```bash
SIM_ENGINE=mock uvicorn app.main:app --reload --port 8000
```

Mock results are always labeled `isDemo: true` and must never be presented as real sims.

### 5. Web UI

```bash
cd apps/web
npm install
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000/api/v1 npm run dev
```

Open http://127.0.0.1:3000

## Docker Compose

```bash
docker compose up --build
```

Services: `web`, `api`, `worker`, `redis`, `db`. The `worker` image builds pinned SimulationCraft.

## Coverage matrix (Midnight 12.1.5)

| Support | Meaning |
|---|---|
| supported | Smoke-oriented MID2 presets (Shadow, Affliction, Assassination, Enhancement) |
| experimental | Runnable MID2/MID1 preset present |
| partial | Limited coverage (reserved) |
| unsupported | No SimC preset on pin (most healers + Augmentation) — still listed in UI |

UI lets you pick talents (import string + hero), toggle abilities, set 1/3/5/10 targets, raid buffs, and run Preview or Monte Carlo sims. Role panels cover tank incoming model, healer damage activity, and Augmentation party contribution estimates.

## Tests

```bash
cd apps/api && python3 -m pytest
cd apps/web && npm test
```

Refresh presets:

```bash
scripts/import_mid2_presets.sh /path/to/simc/profiles/MID2 /path/to/simc/profiles/MID1
scripts/smoke_specs.py
```

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [API.md](docs/API.md)
- [SIMULATION_ENGINE.md](docs/SIMULATION_ENGINE.md)
- [GAME_DATA.md](docs/GAME_DATA.md)
- [DEVELOPMENT.md](docs/DEVELOPMENT.md)
- [TESTING.md](docs/TESTING.md)

## License notes

- Application code in this repository: see repository license / project terms.
- SimulationCraft binary and profiles: **GPL-3.0** — keep as a separate process/image.
- Blizzard Game Data API usage must follow Blizzard Developer API Terms of Use (no monetization of API-sourced features).
