# WoW DPS Lab

Interactive DPS laboratory for **World of Warcraft: Midnight, patch 12.1.5 (Retail)**.

- **Fast Estimate** — deterministic approximation for interactive tuning (`isApproximation: true`)
- **Accurate** — sandboxed **SimulationCraft** Monte Carlo (GPL-3.0)

Coverage: **13 classes / 40 specializations** in SpecRegistry (including Devourer DH, Arcane Mage, tanks, healers, Augmentation).

> Not affiliated with Blizzard Entertainment.

## Stack

| Layer | Tech |
|---|---|
| Web | Next.js, React, TypeScript, Tailwind, Zustand, TanStack Query, Recharts |
| API | FastAPI, Pydantic v2, SQLAlchemy |
| Jobs | Redis + RQ |
| Engine | Pinned SimulationCraft (`engine/simc/SIMC_PIN`) + FastEstimateEngine |
| Data | Versioned catalog + MID1 presets under `packages/game-data` |

## Quick start (local)

### 1. Build SimulationCraft (Accurate only)

```bash
./engine/simc/build.sh
```

### 2. API

```bash
cd apps/api
python3 -m pip install -e ".[dev]"
SIM_ENGINE=mock uvicorn app.main:app --reload --port 8000
```

Mock / Fast Estimate work without a SimC binary. For Accurate:

```bash
SIM_ENGINE=simc uvicorn app.main:app --reload --port 8000
```

### 3. Web UI

```bash
cd apps/web
npm install
npm run dev
```

Open http://127.0.0.1:3000

The UI calls same-origin `/api/v1/*`; Next.js rewrites proxy to the API (`API_PROXY_TARGET`, default `http://127.0.0.1:8000`). If the API is down, class/spec pickers still load from `public/game-catalog.json`.

## Rebuild game registry

```bash
python3 scripts/build_spec_registry.py
```

## Tests

```bash
cd apps/api && SIM_ENGINE=mock python3 -m pytest
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
- Blizzard Game Data API usage must follow Blizzard Developer API Terms of Use.
