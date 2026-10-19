# WoW DPS Lab

Interactive DPS laboratory for **World of Warcraft: Midnight, patch 12.1.5 (Retail)**.

Combat results are produced by **SimulationCraft** (GPL-3.0) via a sandboxed CLI worker — not by invented damage coefficients.

> Not affiliated with Blizzard Entertainment.

## Stack

| Layer | Tech |
|---|---|
| Web | Next.js, React, TypeScript, Tailwind, Zustand, TanStack Query, Recharts |
| API | FastAPI, Pydantic v2, SQLAlchemy |
| Jobs | Redis + RQ |
| Engine | Pinned SimulationCraft (`engine/simc/SIMC_PIN`) |
| Data | Versioned catalog + MID1 presets under `packages/game-data` |

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

## Supported specs (MVP)

| Spec | Support | Notes |
|---|---|---|
| Shadow Priest | supported | MID1 profile |
| Affliction Warlock | supported | MID1 profile |
| Assassination Rogue | supported | MID1 profile |
| Enhancement Shaman | supported | MID1 profile |
| Fury Warrior | experimental | MID1 `talents=` hash fails on pin; retries with `hero_talents=slayer` |
| Havoc Demon Hunter | experimental | same talent-hash caveat |

Unsupported / healer specs are listed in the catalog but cannot be simulated.

## Tests

```bash
cd apps/api && python3 -m pytest
cd apps/web && npm test
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
